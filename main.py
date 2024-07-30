import streamlit as st
import thaiaddress
import time

def main():
    st.title("Thai Address Parser")

    # Address examples
    address_examples = {
        "Example 1": "บสรุปการสั่งซื้อ #36797224 เลขแทร็กกิ้ง 111367972240  ตรวจสอบสถานะสินค้า : https://app.fillgoods.co/orderDetail/46/36797224  1. WT-BG 2'' 1 x 1540 THB  ยอดรวม: 1540 ขนส่งโดย: SCG การชำระเงิน: เก็บเงินปลายทาง   - ชื่อผู้รับ: นายสถาพร จันทะเสน  - ที่อยู่ในการจัดส่ง:  123/1 ม.4 ตำบล/แขวง คอแลน อำเภอ/เขต บุณฑริก จังหวัด อุบลราชธานี  - รหัสไปรษณีย์: 34230  - เบอร์ติดต่อ: 0657376916  - เบอร์ติดต่อสำรอง: -  รบกวนลูกค้า ตรวจสอบรายละเอียดการสั่งซื้อ วิธีการชำระเงินและที่อยู่จัดส่ง  หากมีข้อผิดพลาด สามารถแจ้งเจ้าหน้าที่ได้เลย  สินค้าถึงมือลูกค้าภายใน 2-3 วัน ขอบคุณมากนะคะ ที่มาอุดหนุน",
        "Example 2": "สุรสิทธิ์ชุมสุวรรณ 29 หมู่ 4 ตำบลหนองรี อำเภอเมือง จังหวัดชลบุรี รหัส ไปรษณีย์ 20000 0817585639 เก็บเงินปลายทาง รับ 1 เครื่องครับ 1 490 บาทถูกต้องนะครับ เครื่องตัดหญ้า",
        "Example 3": "จัดส่ง ชนะโชค นามพยัพ 0808674906 25/5/5 หมู่ บ้านเจริญรัตน์ ประชาราษฎร์ 16 แยก2 ตำบลตลาดขวัญ อำเภอเมืองนนทบุรี จังหวัดนนทบุรี 11000 อยากให้ส่งภายใน 2-3 วันเป็นไปได้ไหมครับ ผมต้องการใช้งาน",
        "Example 4": "รบกวนทำใบเสนอราคาให้หน่อยค่ะ บริษัท เฟมไลน์ โปรดักส์ จำกัด (สำนักงานใหญ่) 35/11 ถนนกาญจนาภิเษก แขวงดอกไม้ เขตประเวศ กรุงเทพมหานคร 10250 โทร: 0-2365-5899",
        "Example 5": "ส่งถึงชัยยุทธ ตราชู ธนาคาร กรุงเทพมหานคร จำกัด สาขา จังหวัดนนทบุรี บ้านเลขที่ 26/5 ถนน ประชาราษฏร์ ตำบลตลาดขวัญ อำเภอเมือง จังหวัดนนทบุรี 11000 0958137482 เก็บเงินปลายทาง"
    }

    # Dropdown for selecting example input
    example_selected = st.selectbox("Select an example address or enter your own:", ["กรอกที่อยู่ด้านล่าง"] + list(address_examples.keys()))

    # Text input for custom address or pre-filled example
    if example_selected == "กรอกที่อยู่ด้านล่าง":
        address_input = st.text_input("Enter the address:")
    else:
        address_input = st.text_input("Enter the address:", address_examples[example_selected])

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
