from fastapi import FastAPI, HTTPException
import thaiaddress
import time

app = FastAPI()

default_address = "3 ชุดบาร์คูณ3โซ่7 ราคา 790 บาท(STCS-01-013) นายมงคล 33/2 หมู่ 6 ตำบลคลองเกตุ อำเภอโคกสำโรง จังหวัดลพบุรี 15120 เบอร์โทร 087-117-4624"

@app.get('/parse-address')
async def parse_address():
    start_time = time.time()

    parsed_address = thaiaddress.parse(default_address)
    
    end_time = time.time()
    execution_time = end_time - start_time

    return {
        'parsed_address': parsed_address,
        'execution_time': execution_time
    }
