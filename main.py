import streamlit as st
import thaiaddress
import time

def main():
    st.title("Thai Address Parser")

    address_input = st.text_input("Enter the address:", "3 ชุดบาร์คูณ3โซ่7 ราคา 790 บาท(STCS-01-013) นายมงคล 33/2 หมู่ 6 ตำบลคลองเกตุ อำเภอโคกสำโรง จังหวัดลพบุรี 15120 เบอร์โทร 087-117-4624")

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
