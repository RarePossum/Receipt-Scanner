from http.server import BaseHTTPRequestHandler, HTTPServer
import database_funcs
import ai_actions
import os
import json
import re
import uuid
import cgi # import legacy-cgi for python 3.13 onwards
import magic
from docling.document_converter import DocumentConverter
from transformers import AutoModelForCausalLM, AutoTokenizer

hostName = "localhost"
port = 1234

class Server(BaseHTTPRequestHandler):
    
    tokenizer = AutoTokenizer.from_pretrained("./model")
    model = AutoModelForCausalLM.from_pretrained(
        "./model",
        device_map="auto",  
        torch_dtype="auto"  
    )
        
    converter = DocumentConverter()
    
    def do_GET(self):
        
        filepath = os.path.join(os.path.dirname(__file__), "webpages")
        
        if self.path == "/new":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            filepath = os.path.join(filepath, "new.html")
            f = open(filepath, "rb")
            self.wfile.write(f.read(32768))
                
        elif self.path == "/db":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            filepath = os.path.join(filepath, "db.html")
            f = open(filepath, "rb")
            self.wfile.write(f.read(32768))
                
        elif self.path == "/api/receipts":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()  
                
            receipts = database_funcs.get_receipts()
            self.wfile.write(json.dumps(receipts).encode("utf-8"))
                
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            filepath = os.path.join(filepath, "index.html")
            f = open(filepath, "rb")
            self.wfile.write(f.read(32768))
                        
        elif re.match("\\/[0-9a-f]{8}a", self.path):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                filepath = os.path.join(filepath, "receipt.html")
                f = open(filepath, "rb")
                self.wfile.write(f.read(32768))
                    
        elif re.match("\\/api\\/[0-9a-f]{8}a", self.path):
            id = self.path[-9:]
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()  
            receipt = json.loads(database_funcs.single_receipt(id))
            self.wfile.write(json.dumps(receipt).encode("utf-8"))
             
        
        elif re.match("\\/api\\/delete\\/[0-9a-f]{8}a", self.path):
            id = self.path[-9:]
            database_funcs.delete_receipt(id)
            database_funcs.purge()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()  
                
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()                    
            filepath = os.path.join(filepath, "404.html")
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
            id = str(uuid.uuid4())[:8] + "a"

            if upload_file.filename:
                file_data = upload_file.file.read()
                
                file_type = magic.from_buffer(file_data, mime = True).split("/")[1]
                file_name = id + "." + file_type
                
                with open(file_name, "wb") as f:
                    f.write(file_data)
                
                doc = str(self.converter.convert(file_name).document.export_to_markdown())
                database_funcs.add_file(id, file_type, file_data, doc)
                os.remove(file_name)
                
                messages = ai_actions.create_messages(doc, file_type)                
                content = ai_actions.get_json(messages, self.tokenizer, self.model)                
                content = '{"id": "'+id+'\",'+content[1:]
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            
            else: 
                self.send_response(415)
        
        elif self.path == "/submit":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            form_data = json.loads(post_data.decode("utf-8"))
            database_funcs.create_itemised_receipt(form_data["items"], form_data["id"])
            database_funcs.add_receipt(form_data, form_data["id"])
            database_funcs.purge()
            
            self.send_response(200)
            
        elif re.match("\\/api\\/update\\/[0-9a-f]{8}a", self.path):
            id = self.path[-9:]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            form_data = json.loads(post_data.decode("utf-8"))
            database_funcs.delete_receipt(id)
            database_funcs.create_itemised_receipt(form_data["items"], id)
            database_funcs.add_receipt(form_data, id)
            self.send_response(200)
        
            
        # elif self.path == "/retrain":    

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
    