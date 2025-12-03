import google.generativeai as genai

API_KEY = "AIzaSyCm_YghDygAAWlKet7d-ZU8UlLQuwkcKSc"

genai.configure(api_key=API_KEY)

models = genai.list_models()

for m in models:
    print("Model:", m.name)
    print("  Description:", getattr(m, "display_name", ""))
    print("  Supported methods:", getattr(m, "supported_generation_methods", []))
    print("-" * 50)