# searcher/management/commands/load_cases.py
import os
import re
import json
from django.core.management.base import BaseCommand
from searcher.models import Case

class Command(BaseCommand):
    help = 'Load cases from text and json files'
    
    def handle(self, *args, **kwargs):
        base_dir = 'casefiles'
        txt_dir = os.path.join(base_dir, 'txt')
        json_dir = os.path.join(base_dir, 'json')
        pdf_dir = os.path.join(base_dir, 'pdf')
        counter = 0
        for filename in os.listdir(txt_dir):
            if filename.endswith('.txt'):
                with open(os.path.join(txt_dir, filename), 'r') as f:
                    text_content = f.read()

                json_filename = filename+'.json'
                try:
                    with open(os.path.join(json_dir, json_filename), 'r') as f:
                        counter += 1 
                        content = f.read()
                    
                        # Find the positions of the first `{` and the last `}`
                        start_index = content.find('{')
                        end_index = content.rfind('}') + 1

                        # Check if we found both `{` and `}`
                        if start_index == -1 or end_index == -1 or start_index > end_index:
                            print(json_filename)
                        # Extract the JSON substring
                        json_string = content[start_index:end_index]
                        try:
                            metadata = json.loads(json_string)
                        except:
                            print(json_filename)
                    # Uncomment the following lines if you have PDF files associated
                    pdf_filename = filename.replace('.txt', '.pdf')
                    pdf_path = os.path.join(pdf_dir, pdf_filename)
                    try:
                        Case.objects.create(
                            title = json_filename,
                            summary=metadata['main event'],
                            location=metadata['location'],
                            type=metadata['result'],
                            witnesses=metadata['witnesses'],
                            text_content=text_content,
                            pdf=pdf_path
                        )
                    except:
                        print(json_filename)
                except:
                    print(json_filename)
        self.stdout.write(self.style.SUCCESS('Successfully loaded cases'))
