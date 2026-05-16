from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    source: str
    filename: str = "contract.sol"


class ExplainRequest(BaseModel):
    source: str
    filename: str = "contract.sol"


class ExplainResponse(BaseModel):
    filename: str
    summary: str
    privileged_functions: list[str]
    trust_assumptions: list[str]
