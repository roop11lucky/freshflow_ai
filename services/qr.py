import io, qrcode

def make_qr(batch):
    payload=f"FreshFlow AI | Batch:{batch['batch_id']} | {batch['ingredient']} | Exp:{batch['expiry_date']}"
    img=qrcode.make(payload); buf=io.BytesIO(); img.save(buf,format='PNG'); return buf.getvalue()
