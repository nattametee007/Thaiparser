import streamlit as st
import thaiaddress
import time

def main():
    st.title("Thai Address Parser")

    address_input = st.text_input("Enter the address:", "บสรุปการสั่งซื้อ #36797224 เลขแทร็กกิ้ง 111367972240  ตรวจสอบสถานะสินค้า : https://app.fillgoods.co/orderDetail/46/36797224  1. WT-BG 2'' 1 x 1540 THB  ยอดรวม: 1540 ขนส่งโดย: SCG การชำระเงิน: เก็บเงินปลายทาง   - ชื่อผู้รับ: นายสถาพร จันทะเสน  - ที่อยู่ในการจัดส่ง:  123/1 ม.4 ตำบล/แขวง คอแลน อำเภอ/เขต บุณฑริก จังหวัด อุบลราชธานี  - รหัสไปรษณีย์: 34230  - เบอร์ติดต่อ: 0657376916  - เบอร์ติดต่อสำรอง: -  รบกวนลูกค้า ตรวจสอบรายละเอียดการสั่งซื้อ วิธีการชำระเงินและที่อยู่จัดส่ง  หากมีข้อผิดพลาด สามารถแจ้งเจ้าหน้าที่ได้เลย  สินค้าถึงมือลูกค้าภายใน 2-3 วัน ขอบคุณมากนะคะ ที่มาอุดหนุน")

    if st.button("Parse Address"):
        start_time = time.time()
        try:
            parsed_address = thaiaddress.parse(address_input)
            end_time = time.time()
            execution_time = end_time - start_time

            st.write("**Parsed Address:**")
            if isinstance(parsed_address, dict):
                st.json(parsed_address)
            else:
                st.write(parsed_address)
            st.write(f"**Execution Time:** {execution_time:.4f} seconds")
        except Exception as e:
            st.error("ไม่ใช่ข้อมูลที่อยู่")
            st.write(f"Error details: {e}")

if __name__ == "__main__":
    main()
