# FAI Vegetal

Projeto Python com Streamlit.

## Ambiente virtual

Ativar no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear scripts, use nesta sessao:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

## Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

Para reproduzir exatamente o ambiente validado neste projeto, use o lockfile:

```powershell
python -m pip install -r requirements-lock.txt
```

## Rodar o app

```powershell
streamlit run app.py
```

Sem ativar o ambiente, tambem funciona assim:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
