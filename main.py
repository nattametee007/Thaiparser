import streamlit as st
import thaiaddress
import time

def main():
    st.title("Thai Address Parser")

    # Address example 1
    address_input1 = "บสรุปการสั่งซื้อ #36797224 เลขแทร็กกิ้ง 111367972240  ตรวจสอบสถานะสินค้า : https://app.fillgoods.co/orderDetail/46/36797224  1. WT-BG 2'' 1 x 1540 THB  ยอดรวม: 1540 ขนส่งโดย: SCG การชำระเงิน: เก็บเงินปลายทาง   - ชื่อผู้รับ: นายสถาพร จันทะเสน  - ที่อยู่ในการจัดส่ง:  123/1 ม.4 ตำบล/แขวง คอแลน อำเภอ/เขต บุณฑริก จังหวัด อุบลราชธานี  - รหัสไปรษณีย์: 34230  - เบอร์ติดต่อ: 0657376916  - เบอร์ติดต่อสำรอง: -  รบกวนลูกค้า ตรวจสอบรายละเอียดการสั่งซื้อ วิธีการชำระเงินและที่อยู่จัดส่ง  หากมีข้อผิดพลาด สามารถแจ้งเจ้าหน้าที่ได้เลย  สินค้าถึงมือลูกค้าภายใน 2-3 วัน ขอบคุณมากนะคะ ที่มาอุดหนุน"

    # Address example 2
    address_input2 = "เรียนลูกค้า, สินค้าของท่านได้จัดส่งแล้ว เลขที่พัสดุ: 3344556677  โปรดตรวจสอบสถานะ: https://app.fillgoods.co/orderDetail/47/3344556677  สินค้า: 1. หูฟัง 1 x 2990 THB  ยอดรวม: 2990 การชำระเงิน: ชำระผ่านบัตรเครดิต   - ชื่อผู้รับ: นางสาววิภา วัฒนาภิรมย์  - ที่อยู่ในการจัดส่ง:  78/9 ซ.5 ถ.เจริญนคร แขวง/ตำบล บางลำภูล่าง เขต/อำเภอ คลองสาน จังหวัด กรุงเทพมหานคร  - รหัสไปรษณีย์: 10600  - เบอร์ติดต่อ: 0987654321  โปรดตรวจสอบรายละเอียดการสั่งซื้อและที่อยู่จัดส่งอีกครั้ง"

    # Address example 3
    address_input3 = "ข้อมูลการสั่งซื้อ #78901234 เลขที่พัสดุ: 9876543210 ตรวจสอบได้ที่: https://app.fillgoods.co/orderDetail/48/9876543210 สินค้า: 1. กระเป๋าหนัง 1 x 2500 THB  ยอดรวม: 2500 การชำระเงิน: ชำระปลายทาง   - ชื่อผู้รับ: นายอนุวัฒน์ กุลชาติ  - ที่อยู่ในการจัดส่ง:  45 หมู่ 2 ซอยวัดลาดปลาดุก ตำบล/แขวง บางรักพัฒนา อำเภอ/เขต บางบัวทอง จังหวัด นนทบุรี  - รหัสไปรษณีย์: 11110  - เบอร์ติดต่อ: 0123456789  โปรดตรวจสอบรายละเอียดการสั่งซื้อและที่อยู่จัดส่ง"

    # Select the address to parse
    address_input = st.text_input("Enter the address:", address_input1)

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
