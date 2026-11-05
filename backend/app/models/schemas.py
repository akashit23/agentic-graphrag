from pydantic import BaseModel, Field


class GithubRequest(BaseModel):
    url: str = Field(..., max_length=300)


class RepositoryOut(BaseModel):
    repository_id: str
    repository_name: str
    source_type: str
    source_url: str | None = None
    created_at: str
    status: str
    error: str | None = None
    stats: dict = {}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    repository_id: str
    question: str = Field(..., min_length=3, max_length=2000)
    history: list[ChatMessage] = []


class SourceRef(BaseModel):
    file_path: str
    class_name: str = ""
    function_name: str = ""
    start_line: int
    end_line: int
    kind: str
    found_by: list[str] = []
    score: float = 0.0
    snippet: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    tools_used: list[str]
    files: list[str]
    llm_error: str | None = None


class FileEntry(BaseModel):
    path: str
    language: str
    size: int


class DependencyOut(BaseModel):
    file: str
    depends_on: list[str]
    used_by: list[str]
    impacted: list[str]
    nodes: list[dict]
    edges: list[dict]


class AnalysisOut(BaseModel):
    summary: str
    facts: dict
    llm_used: bool
