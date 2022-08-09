print(list(xlsx_dict["project_publications"]["project.publications.pmid"].fillna('').replace(r'[\n\r]', ' ', regex=True))[0])
