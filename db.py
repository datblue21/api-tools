from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Session, create_engine, select
from typing import List

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Cấu hình cơ sở dữ liệu
DATABASE_URL = "sqlite:///database.db"  # Thay đổi URL theo hệ thống của bạn
engine = create_engine(DATABASE_URL, echo=True)

# Khởi tạo bảng
SQLModel.metadata.create_all(engine)

# Dependency: Tạo session kết nối
def get_session():
    with Session(engine) as session:
        yield session

#thêm sản phẩm
@app.post("/products/", response_model=Product)
def add_product(product: Product, session: Session = Depends(get_session)):
    session.add(product)
    session.commit()
    session.refresh(product)
    return product
#thêm tên sản phẩm
@app.post("/product-names/", response_model=ProductName)
def add_product_name(product_name: ProductName, session: Session = Depends(get_session)):
    session.add(product_name)
    session.commit()
    session.refresh(product_name)
    return product_name

# c Lấy danh sách sản phẩm
@app.get("/products/", response_model=List[Product])
def get_all_products(session: Session = Depends(get_session)):
    statement = select(Product)
    products = session.exec(statement).all()
    return products
    #Lấy sản phẩm theo product_name_id
@app.get("/products/by-name/{product_name_id}", response_model=List[Product])
def get_products_by_name(product_name_id: int, session: Session = Depends(get_session)):
    statement = select(Product).where(Product.product_name_id == product_name_id)
    products = session.exec(statement).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this name")
    return products
    
    #3. Hàm truy vấn liên quan đến đánh giá (rate)
    #3 a) Thêm đánh giá
@app.post("/rates/", response_model=rate)
def add_rate(rate_entry: rate, session: Session = Depends(get_session)):
    session.add(rate_entry)
    session.commit()
    session.refresh(rate_entry)
    return rate_entry    
    #3. b) Lấy đánh giá theo sản phẩm
@app.get("/rates/by-product/{product_id}", response_model=List[rate])
def get_rates_by_product(product_id: int, session: Session = Depends(get_session)):
    statement = select(rate).where(rate.product_id == product_id)
    rates = session.exec(statement).all()
    if not rates:
        raise HTTPException(status_code=404, detail="No rates found for this product")
    return rates
    #3. c) Lấy đánh giá theo review_id
@app.get("/rates/by-review/{review_id}", response_model=List[rate])
def get_rates_by_review(review_id: int, session: Session = Depends(get_session)):
    statement = select(rate).where(rate.review_id == review_id)
    rates = session.exec(statement).all()
    if not rates:
        raise HTTPException(status_code=404, detail="No rates found for this review")
    return rates    
    
    #4. Hàm truy vấn liên quan đến bình luận (ProductReview)
    #4.a) Thêm bình luận
@app.post("/reviews/", response_model=ProductReview)
def add_review(review: ProductReview, session: Session = Depends(get_session)):
    session.add(review)
    session.commit()
    session.refresh(review)
    return review
    #4. b) Lấy bình luận theo sản phẩm
@app.get("/reviews/by-product/{product_id}", response_model=List[ProductReview])
def get_reviews_by_product(product_id: int, session: Session = Depends(get_session)):
    statement = select(ProductReview).where(ProductReview.product_id == product_id)
    reviews = session.exec(statement).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this product")
    return reviews

    #5. Hàm truy vấn kết hợp
    #a) Lấy sản phẩm và các đánh giá của sản phẩm đó
@app.get("/products/{product_id}/rates", response_model=dict)
def get_product_and_rates(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    statement = select(rate).where(rate.product_id == product_id)
    rates = session.exec(statement).all()

    return {"product": product, "rates": rates}
    #5.b) Lấy sản phẩm và các bình luận của sản phẩm đó
@app.get("/products/{product_id}/reviews", response_model=dict)
def get_product_and_reviews(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    statement = select(ProductReview).where(ProductReview.product_id == product_id)
    reviews = session.exec(statement).all()

    return {"product": product, "reviews": reviews}
    #66. Khởi chạy ứng dụng

    #7 Thống kê số lượng đánh giá (count) của sản phẩm theo category và polarity
from sqlalchemy.sql import func
from sqlmodel import select

@app.get("/products/{product_id}/rate-stats", response_model=dict)
def get_rate_stats_by_category(product_id: int, session: Session = Depends(get_session)):
    """
    Lấy số lượng đánh giá theo category và polarity của sản phẩm.
    """
    # Truy vấn nhóm theo category và polarity
    statement = (
        select(rate.category, rate.polarity, func.count())
        .where(rate.product_id == product_id)
        .group_by(rate.category, rate.polarity)
    )
    results = session.exec(statement).all()

    # Chuyển kết quả thành dictionary dễ đọc
    stats = {}
    for category, polarity, count in results:
        if category not in stats:
            stats[category] = {}
        stats[category][polarity] = count

    return {
        "product_id": product_id,
        "rate_stats": stats
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
