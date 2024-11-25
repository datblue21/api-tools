from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import uvicorn

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Load mô hình và tokenizer
model_path = "path_to_your_model"  # Cập nhật đường dẫn mô hình của bạn
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")  # Thay đổi tokenizer nếu cần
model = BertForSequenceClassification.from_pretrained(model_path)
model.eval()  # Đặt chế độ đánh giá để dự đoán

# Nhãn đầu ra
LABELS = ["O", "NEGATIVE", "NEUTRAL", "POSITIVE"]

# Định nghĩa cấu trúc dữ liệu đầu vào
class SentimentRequest(BaseModel):
    text: str

# Endpoint phân tích cảm xúc
@app.post("/analyze")
async def analyze_sentiment(request: SentimentRequest):
    try:
        # Xử lý đầu vào
        input_text = request.text
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True, max_length=512)

        # Dự đoán kết quả
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predictions = torch.argmax(logits, dim=1).tolist()

        # Mapping kết quả sang nhãn
        result = {aspect: LABELS[predictions[i]] for i, aspect in enumerate(["CAMERA", "PERFORMANCE", "FEATURES", "DESIGN", "PRICE", "SCREEN",
       "BATTERY", "GENERAL", "STORAGE", "SER&ACC"])}

        # Chuyển nhãn `O` thành `"null"`
        result = {k: ("null" if v == "O" else v) for k, v in result.items()}

        # Nếu tất cả khía cạnh đều là `null`, trả về "0"
        if all(v == "null" for v in result.values()):
            return {"input_text": input_text, "predictions": "0"}

        # Trả kết quả
        return {"input_text": input_text, "predictions": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

# Khởi chạy ứng dụng
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)