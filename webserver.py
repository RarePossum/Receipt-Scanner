from http.server import BaseHTTPRequestHandler, HTTPServer
import database_funcs
import ai_actions
import os
import json
import uuid
import cgi # import legacy-cgi for python 3.13 onwards
import magic
from docling.document_converter import DocumentConverter
from transformers import AutoModelForCausalLM, AutoTokenizer

hostName = "localhost"
port = 1234
prompt = """Provide a JSON of this receipt, including the store, the quantity of each item with the unit, subtotal, total prices along with date if possible. The format of the json should be similar to the following. Do not include backticks
{
  "store": "name",
  "date": "2002-07-31",
  "items": [
      { "name": "name",
         "price": 12345,
         "quantity": 1.2,
         "subtotal": 123.45,
       }
   ],
 "shipping": 123.45,
  "total": 123.45,
}
Rember to use YYYY-MM-DD date format."""

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        filepath = os.path.join(os.path.dirname(__file__), "webpages")
        match self.path:
            case "/new":
                filepath = os.path.join(filepath, "new.html")
            case "/db":
                filepath = os.path.join(filepath, "db.html")
            case _:
                filepath = os.path.join(filepath, "index.html")
        f = open(filepath, "rb")
        self.wfile.write(f.read(32768))
        
    def do_POST(self):
        if self.path == "/upload":
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            upload_file = form["file"]
            
            if upload_file.filename:
                file_data = upload_file.file.read()
                id = uuid.uuid4()
                file_type = magic.from_buffer(file_data, mime = True).split("/")[1]
                file_name = str(id) + "." + file_type
                
                database_funcs.add_file(str(id), file_type, file_data)
                
                with open(file_name, "wb") as f:
                    f.write(file_data)
                converter = DocumentConverter()
                doc = converter.convert(file_name).document
                os.remove(file_name)
                
                messages = [
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": str(doc.export_to_markdown()) + "This data was extracted from a " + file_type,
                    },
                ]
                
                content = ai_actions.get_json(messages)                
            
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            
            else: 
                self.send_response(415)
        
        # elif self.path == "/submit":
        
        # elif self.path == "retrain":    

if __name__ == "__main__":        
    
    ai_actions.model_preparation()
    
    database_funcs.db_establish()
    
    webServer = HTTPServer((hostName, port), Server)
    print("Server started http://%s:%s" % (hostName, port))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
        
    webServer.server_close()
    print("Server stopped")
    