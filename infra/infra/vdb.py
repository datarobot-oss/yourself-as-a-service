"""
Data resources for YaaS (Yourself as a Service): Dataset, Vector Database, and Deployment.
"""

import os
import tempfile
import time
import zipfile
from pathlib import Path

import pulumi
import pulumi_command as command
import pulumi_datarobot
from datarobot_pulumi_utils.pulumi import export
from datarobot_pulumi_utils.pulumi.stack import PROJECT_NAME

from . import project_dir, use_case

__all__ = [
    "knowledgebase_dataset",
    "vector_database",
]


def create_knowledgebase_zip(knowledgebase_dir: Path = project_dir.parent / "knowledgebase") -> str:
    """Create a zip file of the knowledgebase folder, excluding hidden files."""
    if not knowledgebase_dir.exists():
        raise FileNotFoundError(
            f"Knowledgebase directory not found: {knowledgebase_dir}"
        )

    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / "knowledgebase.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in knowledgebase_dir.rglob("[!.]*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(knowledgebase_dir))

    return str(zip_path)


# Sync knowledgebase from agent memories before creating dataset
sync_knowledgebase = command.local.Command(
    f"Sync Knowledgebase from Agent [{PROJECT_NAME}]",
    create=f"cd {project_dir.parent} && task agent:sync-knowledgebase",
    update=f"cd {project_dir.parent} && task agent:sync-knowledgebase",
    triggers=[str(time.time())],  # Force re-sync on every pulumi up
    opts=pulumi.ResourceOptions(depends_on=[use_case]),
)

# Create Dataset from knowledgebase zip
knowledgebase_zip_path = create_knowledgebase_zip()

knowledgebase_dataset = pulumi_datarobot.DatasetFromFile(
    resource_name=f"YaaS Knowledgebase [{PROJECT_NAME}]",
    file_path=knowledgebase_zip_path,
    use_case_ids=[use_case.id],
    opts=pulumi.ResourceOptions(depends_on=[sync_knowledgebase]),
)

# Create Vector Database with chunking configuration
# Get VDB configuration from environment or use defaults
chunking_method = os.environ.get("VDB_CHUNKING_METHOD", "recursive")
chunk_size = int(os.environ.get("VDB_CHUNK_SIZE", "512"))
chunk_overlap = int(os.environ.get("VDB_CHUNK_OVERLAP_PERCENTAGE", "10"))
embedding_model = os.environ.get("VDB_EMBEDDING_MODEL", "intfloat/e5-large-v2")

vector_database = pulumi_datarobot.VectorDatabase(
    resource_name=f"YaaS VDB [{PROJECT_NAME}]",
    use_case_id=use_case.id,
    dataset_id=knowledgebase_dataset.id,
    chunking_parameters=pulumi_datarobot.VectorDatabaseChunkingParametersArgs(
        chunking_method=chunking_method,
        chunk_size=chunk_size,
        chunk_overlap_percentage=chunk_overlap,
        embedding_model=embedding_model,
    ),
    opts=pulumi.ResourceOptions(depends_on=[use_case, knowledgebase_dataset]),
)

# Export resource IDs
export("YaaS_DATASET_ID", knowledgebase_dataset.id)
export("YaaS_VECTOR_DATABASE_ID", vector_database.id)
