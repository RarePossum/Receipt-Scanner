from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sqlite3
import json
import uuid
import cgi # import legacy-cgi for python 3.13 onwards
import magic
from docling.document_converter import DocumentConverter
from transformers import AutoModelForCausalLM, AutoTokenizer

hostName = "localhost"
serverPort = 1234
prompt = """Provide a JSON of this receipt, including the store, the quantity of each item with the unit, subtotal, total prices along with date if possible. The format of the json should be similar to the following. Do not include backticks
{
  "store": "NAME",
  "date": "YYYY-MM-DD",
  "items": [
      { "name": "name",
         "price": 123.00,
         "quantity": 1,
         "subtotal": 123.00,
       }
   ],
 "shipping": 123.00,
  "total": 123.00,
}"""

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        filepath = os.path.dirname(__file__)
        match self.path:
            case "/new":
                filepath = os.path.join(os.path.join(os.path.dirname(__file__), "webpages"), "new.html")
            case "/db":
                filepath = os.path.join(os.path.join(os.path.dirname(__file__), "webpages"), "db.html")
            case _:
                filepath = os.path.join(os.path.join(os.path.dirname(__file__), "webpages"), "index.html")
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
                self.send_response(200)
                id = uuid.uuid4()
                file_type = magic.from_buffer(file_data, mime = True).split("/")[1]
                file_name = str(id) + "." + file_type
                with open(file_name, "wb") as f:
                    f.write(file_data)
                converter = DocumentConverter()
                doc = converter.convert(file_name).document
                os.remove(file_name)
                
                tokenizer = AutoTokenizer.from_pretrained("./model")
                model = AutoModelForCausalLM.from_pretrained(
                    "./model",
                    device_map="auto",  
                    torch_dtype="auto"  
                )
                
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
                
                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize = False,
                    add_generation_prompt = True,
                    enable_thinking = False,
                )
                
                model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

                generated_ids = model.generate(
                    **model_inputs,
                    max_new_tokens=32768
                )
                output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 
                content = tokenizer.decode(output_ids, skip_special_tokens=True).strip("\n")
                print(content)
            
            else: 
                self.send_response(400)
        
        # elif self.path == "/submit":
        
        # elif self.path == "retrain":    

if __name__ == "__main__":        

    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS files (id VARCHAR(36) PRIMARY KEY, file_type VARCHAR(6), file BLOB(32768));")
    cur.execute("CREATE TABLE IF NOT EXISTS receipts (id VARCHAR(36) PRIMARY KEY, merchant TEXT, date TEXT, total INTEGER, is_work INTEGER, receipt VARCHAR(32768));")
    
    filepath = os.path.join(os.path.dirname(__file__), "model")
    if not os.path.isdir(filepath):  
        print("Downloading Qwen3-0.6B as no model found")
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
        model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B")
        tokenizer.save_pretrained("./model")
        model.save_pretrained("./model")
    
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
        
    webServer.server_close()
    print("Server stopped")