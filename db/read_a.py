import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.document("靜宜資管2026B/tcyang2")
doc = doc_ref.get()
result = doc.to_dict()
print(result)
print(result["name"], result["lab"])
