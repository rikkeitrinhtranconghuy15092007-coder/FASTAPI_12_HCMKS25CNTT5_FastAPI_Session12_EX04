import uvicorn
from fastapi import FastAPI, status, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from typing import Optional

DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/ecommerce_db"

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StudentModel(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Quản Lý Học Viên - Chức năng Xóa")

class StudentDataResponse(BaseModel):
    id: int
    full_name: str
    email: str

class DeleteStudentResponse(BaseModel):
    message: str
    data: StudentDataResponse

def delete_student_service(db: Session, student_id: int):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Học viên không tồn tại trong hệ thống"
        )
        
    student_data = {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email
    }
    
    try:
        db.delete(student)
        db.commit()
        return student_data
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi xóa dữ liệu: {str(e)}"
        )

@app.delete("/students/{student_id}", status_code=status.HTTP_200_OK, response_model=DeleteStudentResponse)
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    deleted_data = delete_student_service(db, student_id)
    return DeleteStudentResponse(
        message="Xóa học viên thành công",
        data=StudentDataResponse(**deleted_data)
    )

@app.post("/init-students", status_code=status.HTTP_201_CREATED)
async def init_students(db: Session = Depends(get_db)):
    if db.query(StudentModel).count() == 0:
        s1 = StudentModel(full_name="Nguyen Van A", email="vana@gmail.com")
        s2 = StudentModel(full_name="Tran Thi B", email="thib@gmail.com")
        db.add_all([s1, s2])
        db.commit()
        return {"message": "Khởi tạo thành công học viên Nguyen Van A (ID: 1) để chạy thử nghiệm!"}
    return {"message": "Database đã có dữ liệu học viên."}