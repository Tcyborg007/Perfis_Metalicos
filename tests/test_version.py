from perfis_metalicos import ENGINE_VERSION, __version__
from perfis_metalicos.domain import VerificationResult, VerificationStatus


def test_engine_version_is_single_source_for_results():
    result = VerificationResult(
        check_id="VERSION",
        demand=None,
        resistance_or_limit=None,
        utilization=None,
        status=VerificationStatus.NOT_CHECKED,
        justification="Teste da versão centralizada.",
    )
    assert ENGINE_VERSION == __version__ == "0.2.0"
    assert result.engine_version == ENGINE_VERSION
