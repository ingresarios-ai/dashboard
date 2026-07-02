import urllib.request
import urllib.parse
import json
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# Supabase reference configuration
SUPABASE_URL = "https://tfwvvsvoimgnwjodfwlh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmd3Z2c3ZvaW1nbndqb2Rmd2xoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2OTg0NzgsImV4cCI6MjA5NDI3NDQ3OH0.fw1p2llL3wR4g8oa-J1KbljqrjckbuLg7KvxLDSKPuo"

def main():
    print("\n=== Sincronizador de Dashboards — Boost Agency ===")
    
    # 1. Prompt parameters with default values
    client = input("Cliente (default: ingresarios): ").strip().lower() or "ingresarios"
    product = input("Producto/Embudo (ej: launch, vsl; default: launch): ").strip().lower() or "launch"
    project_date = input("Fecha de proyecto (ej: ago26, jul26; default: ago26): ").strip().lower() or "ago26"
    start_date = input("Fecha de inicio (YYYY-MM-DD, default: 2026-06-30): ").strip() or "2026-06-30"
    end_date = input("Fecha de fin (YYYY-MM-DD, default: 2026-07-31): ").strip() or "2026-07-31"
    currency = input("Moneda de reporte (default: COP): ").strip().upper() or "COP"

    payload = {
        "client": client,
        "product": product,
        "project_date": project_date,
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency
    }

    url = f"{SUPABASE_URL}/functions/v1/sync-dashboard"
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    print("\n[+] Consultando datos de Windsor.ai y generando dashboard en la nube...")
    
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            
            if res_json.get("success"):
                html_content = res_json.get("html")
                file_name = res_json.get("fileName")
                public_url = res_json.get("publicUrl")
                
                # 2. Save locally in correct folder
                output_dir = f"dashboards - métricas/{client}"
                os.makedirs(output_dir, exist_ok=True)
                
                local_path = os.path.join(output_dir, file_name)
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                print("\n[✔] ¡Dashboard generado con éxito!")
                print(f"[-] Guardado localmente en: {local_path}")
                if public_url:
                    print(f"[-] Enlace en la nube (hosted): {public_url}")

                # 3. Update index.html dynamically to include the new link
                index_path = "index.html"
                if os.path.exists(index_path):
                    with open(index_path, "r", encoding="utf-8") as f:
                        index_content = f.read()
                    
                    card_href = f"dashboards - métricas/{client}/{file_name}"
                    card_html = f"""    <!-- CARD: {client}_{product}_{project_date} -->
    <div class="card">
      <span class="client-badge">{client}</span>
      <h3>Embudo: {product.upper()} ({project_date})</h3>
      <p class="date">Rango: {start_date} - {end_date}</p>
      <a href="{card_href}" class="btn">Ver Dashboard</a>
    </div>"""
                    
                    if card_href not in index_content:
                        grid_tag = '<div class="grid">'
                        if grid_tag in index_content:
                            index_content = index_content.replace(grid_tag, f"{grid_tag}\n{card_html}")
                            with open(index_path, "w", encoding="utf-8") as f:
                                f.write(index_content)
                            print("[-] Portal index.html actualizado con el nuevo enlace.")

                # 4. Git commit and push automatically to trigger Vercel deploy
                if os.path.exists(".git"):
                    print("\n[+] Detectado repositorio Git. Subiendo cambios a GitHub...")
                    try:
                        import subprocess
                        subprocess.run(["git", "add", "."], check=True)
                        commit_msg = f"feat: auto-sync dashboard {client} {product} {project_date}"
                        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                        subprocess.run(["git", "push", "origin", "main"], check=True)
                        print("[✔] ¡Cambios subidos a GitHub con éxito! (Despliegue de Vercel iniciado)")
                    except Exception as git_err:
                        print(f"[⚠️] No se pudo hacer push automático a git: {git_err}")

            else:
                print("\n[❌] Error devuelto por la función:", res_json.get("error"))
                
    except urllib.error.HTTPError as e:
        print("\n[❌] Error HTTP en la ejecución:", e.code)
        print("[-] Detalle:", e.read().decode("utf-8"))
    except Exception as e:
        print("\n[❌] Error inesperado:", e)

if __name__ == "__main__":
    main()
