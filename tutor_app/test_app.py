from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Тест</title></head>
    <body>
        <h1 style="color: green;">✅ Сервер работает!</h1>
        <p>FastAPI успешно запущен.</p>
    </body>
    </html>
    """