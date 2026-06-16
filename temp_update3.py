file_path = "D:/REPOSITORIO_GIT/laudonr13/backend/src/api/v1/formularios.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# FormPage
content = content.replace("FormPage.form_template_id", "FormPage.formulario_id")
content = content.replace("FormPage.label", "FormPage.nome")
content = content.replace("form_template_id=form_template_id", "formulario_id=form_template_id")
content = content.replace("label=page_name", "nome=page_name")

# FormField
content = content.replace("FormField.form_page_id", "FormField.pagina_id")
content = content.replace("form_page_id=page_id", "pagina_id=page_id")
content = content.replace(label=row[label], rotulo=row[rotulo])
content = content.replace(type=row[tipo], tipo=row[tipo])
content = content.replace(config=row[config], configuracao=row[configuracao])

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("formularios.py atualizado!")
