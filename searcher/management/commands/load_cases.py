import os
import json
from django.core.management.base import BaseCommand
from searcher.models import Case
from django.db import IntegrityError, DatabaseError

class Command(BaseCommand):
    help = 'Load cases from text and json files'
    
    def handle(self, *args, **kwargs):
        base_dir = 'casefiles/'
        txt_dir = os.path.join(base_dir, 'txt')
        json_dir = os.path.join(base_dir, 'json')
        pdf_dir = os.path.join(base_dir, 'pdf')
        cases_to_create = []
        counter = 0

        for filename in os.listdir(txt_dir):
            if filename.endswith('.txt'):
                with open(os.path.join(txt_dir, filename), 'r') as f:
                    text_content = f.read()

                json_filename = filename + '.json'
                try:
                    with open(os.path.join(json_dir, json_filename), 'r') as f:
                        counter += 1 
                        content = f.read()
                    
                        # Find the positions of the first `{` and the last `}`
                        start_index = content.find('{')
                        end_index = content.rfind('}') + 1

                        # Check if we found both `{` and `}`
                        if start_index == -1 or end_index == -1 or start_index > end_index:
                            print(f"Invalid JSON structure in file: {json_filename}")
                            continue

                        # Extract the JSON substring
                        json_string = content[start_index:end_index]
                        try:
                            metadata = json.loads(json_string)
                        except json.JSONDecodeError:
                            print(f"JSON decode error in file: {json_filename}")
                            continue
                    
                    # Uncomment the following lines if you have PDF files associated
                    pdf_filename = filename.replace('.txt', '.pdf')
                    pdf_path = os.path.join(pdf_dir, pdf_filename)
                    
                    cases_to_create.append(
                        Case(
                            title=json_filename,
                            summary=metadata.get('main event', ''),
                            location=metadata.get('location', ''),
                            type=metadata.get('result', ''),
                            witnesses=metadata.get('witnesses', ''),
                            text_content=text_content,
                            pdf=pdf_path
                        )
                    )
                except FileNotFoundError:
                    print(f"File not found: {json_filename}")
                except Exception as e:
                    print(f"An error occurred with file {json_filename}: {str(e)}")

        try:
            Case.objects.bulk_create(cases_to_create)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(cases_to_create)} cases'))
        except (IntegrityError, DatabaseError) as db_error:
            self.stdout.write(self.style.ERROR(f"Database error: {str(db_error)} in {json_filename}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {str(e)}"))