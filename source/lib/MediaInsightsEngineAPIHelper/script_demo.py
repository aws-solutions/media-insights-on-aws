from rich.console import Console
from rich.syntax import Syntax
from rich import print
import time


def pretty_printer(item):
    syntax = Syntax(item, "python", theme="monokai", line_numbers=False, background_color='black')
    console = Console()
    console.print(syntax)


# import_statement = 'from MediaInsightsEngineAPIHelper import WorkflowAPI'

import_statement = "To begin, let us instantiate an instance\n of the MIE API helper\n"

api = 'mie_api = MIE()'

first = '\nNow we can create a video preprocessing stage\n for the start of our workflow\n'

preprocess_0 = 'preprocess_video_stage = {"Name": "PreprocessVideo", \n"Operations": ["Mediainfo", "Thumbnail"]}'

preprocess_1 = 'mie_api.create_stage(preprocess_video_stage)'

ml_stage = '\nAfter that, we can create a machine learning\n analysis stage\n'

ml_stage_body = '''
machine_learning_stage = {
    "Name": "MlVideo", 
    "Operations": [
      "celebrityRecognition", 
      "contentModeration",
      "faceDetection",
      "labelDetection", 
      "shotDetection", 
      "textDetection", 
      "technicalCueDetection"
    ]
}
'''

ml_stage_exec = 'mie_api.create_stage(machine_learning_stage)'

then = '\nThen, we will combine both of these stages into a\n sequential workflow that can be executed \n'

analyze = '''
analyze_video_workflow = {
    "Name": "AnalyzeVideo", 
    "StartAt": "PreprocessVideo",
    "Stages": {
      "PreprocessVideo": {"Next": "MlVideo"}, 
      "MlVideo": {"End": True}
    }
}
'''

analyze_body = '''
mie_api.create_workflow(analyze_video_workflow)
'''

final = '''
\nAnd finally, we execute the workflow\n
'''

final_body = '''
workflow_execution = {
    "Name": "AnalyzeVideo",
    "Input": {
        "Media": {
            "Video": {
                "S3Bucket": "mie-dataplane",
                "S3Key": 'upload/' + 'video.mp4'
            }
        }
    }
}
'''

final_start = '''
mie_api.start_workflow(workflow_execution)
'''

print("[bold red]{import_statement}[/bold red]".format(import_statement=import_statement))
time.sleep(3)
print(api) #pretty
time.sleep(2)
print("[bold red]{first}[/bold red]".format(first=first))
time.sleep(4)
print(preprocess_0) # pretty
time.sleep(4)
print(preprocess_1) # pretty
time.sleep(2)
print("[bold red]{ml_stage}[/bold red]".format(ml_stage=ml_stage))
time.sleep(3)
print(ml_stage_body) # pretty
time.sleep(4)
print(ml_stage_exec) # pretty
time.sleep(2)
print("[bold red]{then}[/bold red]".format(then=then))
time.sleep(4)
print(analyze) # pretty
time.sleep(3)
print(analyze_body) # pretty
time.sleep(3)
print("[bold red]{final}[/bold red]".format(final=final))
time.sleep(3)
print(final_body) # pretty
time.sleep(3)
print(final_start) # pretty
time.sleep(2)
print('\n')



# print("After that, we can create a machine learning analysis stage")
# machine_learning_stage = {"Name": "MlVideo",
#                           "Operations": ["celebrityRecognition", "contentModeration", "faceDetection", "labelDetection",
#                                          "shotDetection", "textDetection", "technicalCueDetection"]}
# mie_api.create_stage(machine_learning_stage)
#
# print("Then, we will combine both of these stages into a sequential workflow that can be executed")
# analyze_video_workflow = {"Name": "AnalyzeVideo", "StartAt": "PreprocessVideo",
#                           "Stages": {"PreprocessVideo": {"Next": "MlVideo"}, "MlVideo": {"End": True}}}
# mie_api.create_workflow(analyze_video_workflow)
#
#
# print("And finally, we now execute the workflow")
# workflow_execution = {
#     "Name": "AnalyzeVideo",
#     "Input": {
#         "Media": {
#             "Video": {
#                 "S3Bucket": "mie-dataplane-jasee0ne7egz",
#                 "S3Key": 'upload/' + 'test_video.mp4'
#             }
#         }
#     }
# }
# mie_api.start_workflow(workflow_execution)
