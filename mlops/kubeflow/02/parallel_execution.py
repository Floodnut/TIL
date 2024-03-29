import kfp
from kfp import dsl
from kubeflow_host import KubeflowHost
from dotenv import dotenv_values


EXPERIMENT_NAME = 'Parallel execution'        # Name of the experiment in the UI
BASE_IMAGE = "python:3.7"

def gcs_download_op(url):
    return dsl.ContainerOp(
        name='GCS - Download',
        image='google/cloud-sdk:272.0.0',
        command=['sh', '-c'],
        arguments=['gsutil cat $0 | tee $1', url, '/tmp/results.txt'],
        file_outputs={
            'data': '/tmp/results.txt',
        }
    )


def echo2_op(text1, text2):
    return dsl.ContainerOp(
        name='echo',
        image='library/bash:4.4.23',
        command=['sh', '-c'],
        arguments=['echo "Text 1: $0"; echo "Text 2: $1"', text1, text2]
    )


@dsl.pipeline(
    name='Parallel pipeline',
    description='Download two messages in parallel and prints the concatenated result.'
)
def download_and_join(
        url1='gs://ml-pipeline-playground/shakespeare1.txt',
        url2='gs://ml-pipeline-playground/shakespeare2.txt'
):
    """A three-step pipeline with first two running in parallel."""

    download1_task = gcs_download_op(url1)
    download2_task = gcs_download_op(url2)

    echo_task = echo2_op(download1_task.output, download2_task.output)


if __name__ == '__main__':
    env = dotenv_values('.env')
    
    kubeflow_host = KubeflowHost(
        env.get("HOST"),
        env.get("USERNAME"),
        env.get("PASSWORD"),
        env.get("NAMESPACE")
    )
    kfp_client = kubeflow_host.get_kfp_client()
    
    # kfp.compiler.Compiler().compile(download_and_join, __file__ + '.zip')
    kfp_client.create_run_from_pipeline_func(
        download_and_join,
        arguments={},
        experiment_name=EXPERIMENT_NAME)
