"""Memorial de cálculo auditável para o núcleo NBR 8800:2024.

Este módulo não recalcula resistências: ele apresenta, com fórmulas e
substituições numéricas, os valores intermediários produzidos por
``calculos_nbr8800_2024``. Unidades-base: kN e cm.
"""

from __future__ import annotations

import html
import math
from numbers import Real


def _n(value, digits=3):
    if value is None:
        return "N/A"
    # Propriedades vindas do pandas podem ser numpy.int64/numpy.float64.
    # numbers.Real abrange esses escalares sem mascarar valores não numéricos.
    if not isinstance(value, Real) or not math.isfinite(value):
        return "∞" if value == math.inf else "N/A"
    return f"{value:.{digits}f}"


def _esc(value):
    return html.escape(str(value))


def _status_class(status):
    return "pass" if status == "APROVADO" else "pending" if status in {"N/A", "NÃO VERIFICADO"} else "fail"


def _eq(*lines):
    """Organiza equações relacionadas em linhas distintas e alinhadas."""
    aligned = []
    for line in lines:
        if "&" not in line and "=" in line:
            line = line.replace("=", "&=", 1)
        aligned.append(line)
    return r"\begin{aligned}" + r"\\[8pt]".join(aligned) + r"\end{aligned}"


def _eq_lines(block):
    prefix, suffix = r"\begin{aligned}", r"\end{aligned}"
    if block.startswith(prefix) and block.endswith(suffix):
        block = block[len(prefix):-len(suffix)]
        lines = block.split(r"\\[8pt]")
    else:
        lines = [block]
    return [line.replace("&=", "=").strip() for line in lines if line.strip()]


def _equation_chain(symbolic, numeric):
    """Apresenta cada equação e sua aplicação numérica em linhas separadas."""
    symbolic_lines = _eq_lines(symbolic)
    numeric_lines = _eq_lines(numeric)
    if len(symbolic_lines) != len(numeric_lines):
        raise ValueError(
            "Etapa com encadeamento incompleto: quantidade de equações simbólicas "
            f"({len(symbolic_lines)}) diferente das substituições ({len(numeric_lines)})."
        )
    return "".join(
        f"""
        <div class="equation-pair">
          <div class="equation-line equation-symbolic">$${symbol}$$</div>
          <div class="equation-line equation-numeric">$${number}$$</div>
        </div>"""
        for symbol, number in zip(symbolic_lines, numeric_lines)
    )


def _equation_heading(step_title, decision, explicit=None):
    if explicit:
        return explicit
    regime = str(decision or "").lower()
    if "inelást" in regime:
        return f"Equação inelástica — {step_title}"
    if "elást" in regime:
        return f"Equação elástica — {step_title}"
    if "plást" in regime or "escoamento" in regime:
        return f"Equação plástica — {step_title}"
    return None


def _theory_panel(title, objective, variables, concepts, reference):
    variable_rows = "".join(
        f"<tr><td>\\({_esc(symbol)}\\)</td><td>{_esc(description)}</td><td>{_esc(unit)}</td></tr>"
        for symbol, description, unit in variables
    )
    concept_cards = "".join(
        f'<div class="theory-concept"><h5>{_esc(name)}</h5><p>{_esc(text)}</p></div>'
        for name, text in concepts
    )
    return f"""
    <details class="theory-panel">
      <summary><span>Fundamentação e variáveis</span><strong>{_esc(title)}</strong></summary>
      <div class="theory-content">
        <h4>Objetivo da verificação</h4>
        <p>{_esc(objective)}</p>
        <h4>Dicionário de símbolos</h4>
        <div class="variable-table-wrap"><table class="variable-table">
          <thead><tr><th>Símbolo</th><th>Definição física</th><th>Unidade adotada</th></tr></thead>
          <tbody>{variable_rows}</tbody>
        </table></div>
        <h4>Conceitos e interpretação</h4>
        <div class="theory-grid">{concept_cards}</div>
        <div class="norm-ref">Base normativa: {_esc(reference)}</div>
      </div>
    </details>"""


def _beam_theory():
    return _theory_panel(
        "Ações, combinações e análise da viga",
        "Transformar ações características em ações de cálculo e obter, por equilíbrio e compatibilidade, reações, cortantes e momentos na mesma seção da viga.",
        [
            ("B", "largura de influência tributária da viga", "m"),
            (r"b_{esq},\;b_{dir}", "larguras tributárias totais à esquerda e à direita; cada lado contribui pela metade", "m"),
            (r"g_k,\;q_k", "ações permanente e variável características por área", "kN/m²"),
            (r"q_{G,k},\;q_{Q,k},\;q_{pp,k}", "ações lineares características e peso próprio", "kN/m"),
            (r"\gamma_g,\;\gamma_q,\;\gamma_{pp}", "coeficientes de ponderação do ELU", "adimensional"),
            (r"P_d,\;q_d", "força pontual e ação distribuída de cálculo", "kN; kN/m"),
            (r"L,\;a,\;b", "comprimento da viga, posição da força pontual e distância complementar L − a", "cm ou m"),
            ("x", "coordenada longitudinal medida desde a extremidade esquerda", "cm ou m"),
            (r"R_A,\;R_B", "reações verticais nos vínculos A e B", "kN"),
            (r"M_A,\;M_B", "momentos de extremidade resultantes das condições de contorno", "kN·m"),
            (r"M(x),\;V(x)", "momento fletor e força cortante na seção x", "kN·m; kN"),
            (r"H(x-a),\;\langle x-a\rangle", "funções de singularidade que ativam a força após x = a", "adimensional; comprimento"),
        ],
        [
            ("Valor característico", "Representa a intensidade de referência da ação antes da ponderação de segurança."),
            ("Valor de cálculo", "É obtido pela combinação normativa das parcelas características e é utilizado nas verificações de ELU."),
            ("Análise conjunta", "Ações distribuídas e pontuais atuam simultaneamente; máximos localizados em seções diferentes não são somados."),
            ("Convenção de sinais", "O núcleo conserva sinais para montar os diagramas e usa o maior valor absoluto na verificação resistente."),
        ],
        "ABNT NBR 8800:2024, 4.8.7.2 e 4.8.7.3; Tabelas 1 e 2; modelo elástico de primeira ordem declarado.",
    )


def _cb_theory():
    return _theory_panel(
        "Fator de modificação do diagrama de momento Cb",
        "Representar o efeito favorável ou desfavorável do gradiente de momento sobre a flambagem lateral com torção no trecho sem contenção lateral.",
        [
            ("L_b", "comprimento entre pontos que impedem o deslocamento lateral da mesa comprimida", "cm ou m"),
            ("M_{max}", "máximo momento fletor em módulo no trecho Lb", "kN·m"),
            (r"M_A,\;M_B,\;M_C", "momentos em módulo nos quartos, no meio e em três quartos de Lb", "kN·m"),
            ("C_b", "fator de modificação associado ao diagrama de momento", "adimensional"),
        ],
        [
            ("Trecho destravado", "É o segmento efetivamente livre para deslocamento lateral e torção; não deve ser confundido automaticamente com o vão total."),
            ("Momentos em módulo", "A equação emprega os valores absolutos nas quatro posições prescritas do trecho analisado."),
            ("Uso em FLT", "Cb altera o momento crítico de flambagem lateral com torção, mas não substitui a definição correta de Lb e das contenções."),
        ],
        "ABNT NBR 8800:2024, 5.4.2.3 a 5.4.2.5.",
    )


def _flexure_theory():
    return _theory_panel(
        "Flexão: plastificação, FLT, FLM, FLA e Anexo E",
        "Determinar a resistência de cálculo ao momento fletor considerando plastificação, instabilidades global e locais, alma esbelta e eventual ruptura da mesa tracionada.",
        [
            (r"f_y,\;f_u", "resistências ao escoamento e à ruptura do aço", "kN/cm²"),
            ("E", "módulo de elasticidade longitudinal do aço", "kN/cm²"),
            (r"b_f,\;t_f", "largura e espessura da mesa", "cm"),
            (r"h,\;t_w", "altura livre e espessura da alma", "cm"),
            (r"W_x,\;Z_x", "módulos resistente elástico e plástico no eixo forte", "cm³"),
            (r"M_{pl},\;M_r,\;M_{cr}", "momentos plástico, residual/de transição e crítico elástico", "kN·m"),
            (r"\lambda,\;\lambda_p,\;\lambda_r", "esbeltez do elemento e limites plástico e elástico", "adimensional"),
            (r"I_y,\;J,\;C_w", "inércia no eixo fraco, constante de torção e empenamento", "cm⁴; cm⁴; cm⁶"),
            (r"L_b,\;C_b", "comprimento destravado e fator de gradiente de momento", "cm; adimensional"),
            (r"\chi_{LT}", "fator de redução associado à FLT", "adimensional"),
            (r"k_c,\;k_{pg}", "coeficientes de flambagem da mesa e redução por alma esbelta", "adimensional"),
            (r"\sigma_r", "tensão residual adotada nas transições de flambagem", "kN/cm²"),
            (r"A_{fg},\;A_{fn},\;Y_t", "áreas bruta e líquida da mesa tracionada e coeficiente de ruptura", "cm²; cm²; adimensional"),
            (r"W_{xc},\;I_{yc},\;A_{yc},\;r_{yc}", "propriedades associadas à mesa comprimida no Anexo E", "cm³; cm⁴; cm²; cm"),
            (r"\gamma_{a1},\;\gamma_{a2}", "coeficientes de resistência para escoamento/instabilidade e ruptura", "adimensional"),
        ],
        [
            ("Regime plástico ou compacto", "A esbeltez não excede λp; o elemento consegue desenvolver a resistência plástica prevista antes da flambagem local."),
            ("Regime inelástico ou semicompacto", "A esbeltez está entre λp e λr; parte da seção escoa antes da instabilidade e a resistência é interpolada."),
            ("Regime elástico ou esbelto", "A esbeltez excede λr; a instabilidade ocorre predominantemente antes do escoamento generalizado e governa Mcr."),
            ("FLT", "Instabilidade global com deslocamento lateral da mesa comprimida e torção da seção no trecho Lb."),
            ("FLM", "Flambagem local da mesa comprimida, controlada principalmente pela largura da meia mesa dividida pela espessura tf."),
            ("FLA e Anexo E", "A alma pode ser compacta, semicompacta ou esbelta; almas esbeltas soldadas exigem o procedimento específico do Anexo E."),
            ("Estado governante", "A resistência final é a menor entre todos os estados-limites aplicáveis e o limite geral de resistência."),
        ],
        "ABNT NBR 8800:2024, 5.4.2, 5.4.2.6, Anexo D e Anexo E.",
    )


def _shear_theory():
    return _theory_panel(
        "Cisalhamento da alma e enrijecedores transversais",
        "Classificar a alma ao cisalhamento, determinar o coeficiente de flambagem kv e calcular VRd no regime de escoamento, flambagem inelástica ou flambagem elástica.",
        [
            (r"d,\;h,\;t_w", "altura total, altura livre e espessura da alma", "cm"),
            ("a", "distância entre enrijecedores transversais", "cm"),
            (r"b,\;t", "largura e espessura da chapa do enrijecedor", "cm"),
            ("k_v", "coeficiente de flambagem da alma ao cisalhamento", "adimensional"),
            (r"\lambda,\;\lambda_p,\;\lambda_r", "esbeltez da alma e limites entre os três regimes", "adimensional"),
            (r"E,\;f_y,\;\gamma_{a1}", "módulo de elasticidade, escoamento e coeficiente de resistência", "kN/cm²; kN/cm²; adimensional"),
            (r"V_{pl},\;V_{Rd}", "força cortante plástica nominal e resistência de cálculo", "kN"),
            (r"I_{st},\;I_{req}", "inércia fornecida e mínima requerida ao enrijecedor", "cm⁴"),
            ("j", "parâmetro da inércia mínima corrigido pela Errata 1:2025", "adimensional"),
        ],
        [
            ("Escoamento", "Para λ ≤ λp, a alma alcança a força cortante plástica antes de perder estabilidade."),
            ("Flambagem inelástica", "Para λp < λ ≤ λr, ocorre redução proporcional à razão entre λp e λ."),
            ("Flambagem elástica", "Para λ > λr, a resistência decresce com o quadrado da razão entre λp e λ."),
            ("Enrijecedor eficaz", "Somente altera kv quando soldagem, limite de esbeltez da chapa e inércia mínima forem todos atendidos."),
        ],
        "ABNT NBR 8800:2024, 5.4.3.1; ABNT NBR 8800:2024/Er1:2025.",
    )


def _local_theory():
    return _theory_panel(
        "Forças transversais localizadas na alma",
        "Verificar a região da alma sob reações e forças concentradas contra escoamento local, enrugamento e flambagem lateral, adotando a menor resistência aplicável.",
        [
            (r"\ell_n", "comprimento de atuação da força transversal", "cm"),
            ("k", "distância da face externa da mesa ao pé do filete ou início da alma livre", "cm"),
            (r"d,\;h,\;b_f,\;t_f,\;t_w", "geometria total, alma e mesa da seção analisada", "cm"),
            (r"E,\;f_y,\;\gamma_{a1}", "módulo de elasticidade, escoamento e coeficiente de resistência", "kN/cm²; kN/cm²; adimensional"),
            (r"F_{Sd},\;F_{Rd}", "força localizada solicitante e resistência de cálculo", "kN"),
            (r"\ell", "comprimento destravado local da região analisada", "cm"),
            (r"\eta", "parâmetro geométrico para flambagem lateral da alma", "adimensional"),
            ("C_r", "coeficiente dependente do nível de momento na seção carregada", "kN/cm²"),
            (r"M_r,\;k_{pg}", "momento de início de escoamento e redução por alma esbelta, quando aplicável", "kN·m; adimensional"),
        ],
        [
            ("Escoamento local", "Esmagamento/escoamento da alma junto à mesa carregada; a expressão depende da proximidade da extremidade."),
            ("Enrugamento", "Instabilidade localizada da alma sob compressão transversal, sensível às razões entre ℓn e d e entre tw e tf."),
            ("Flambagem lateral", "Só é aplicável quando pode existir movimento lateral relativo entre as mesas na região da força."),
            ("Detalhamento", "Quando a resistência da alma é insuficiente, enrijecedores e soldas devem ser dimensionados e detalhados conforme as exigências específicas."),
        ],
        "ABNT NBR 8800:2024, 5.7.3 a 5.7.5 e 5.7.9.",
    )


def _els_theory():
    return _theory_panel(
        "Estado-limite de serviço de deslocamento",
        "Calcular o deslocamento vertical sob a combinação de serviço apropriada e compará-lo ao limite funcional aplicável ao uso da viga.",
        [
            (r"q_s,\;P_s", "ação distribuída e força pontual da combinação de serviço", "kN/m; kN"),
            (r"\psi_1,\;\psi_2", "fatores de combinação frequente e quase permanente", "adimensional"),
            (r"E,\;I_x", "módulo de elasticidade e inércia no eixo de flexão", "kN/cm²; cm⁴"),
            (r"v(x),\;\delta_{max}", "linha elástica e maior deslocamento em módulo", "cm"),
            ("C_1", "constante de integração determinada pelas condições de contorno", "kN·cm²"),
            (r"M_A,\;R_A", "momento e reação na extremidade esquerda usados na integração", "kN·cm; kN"),
            (r"x,\;a", "coordenada avaliada e posição da força pontual", "cm"),
            (r"L_{ref},\;n", "comprimento de referência e divisor do limite de deslocamento", "cm; adimensional"),
        ],
        [
            ("ELU × ELS", "Coeficientes de segurança do ELU não são usados na flecha; o ELS utiliza combinações rara, frequente ou quase permanente."),
            ("Rigidez elástica", "A curvatura é governada por E·Ix; maior rigidez reduz o deslocamento para a mesma ação."),
            ("Balanços", "O comprimento de referência para o limite é o dobro do comprimento teórico do balanço."),
            ("Alvenaria", "Quando declarada, o limite absoluto adicional de 15 mm é comparado ao limite relativo e o menor governa."),
        ],
        "ABNT NBR 8800:2024, 4.8.7.3 e Anexo B.",
    )


_STEP_THEORY = {
    "Esforços informados": (
        "Fundamento do procedimento",
        "Neste modo, os esforços solicitantes já representam o resultado de uma análise estrutural externa e de uma combinação de ações previamente executada. O aplicativo não dispõe das ações elementares, das condições de contorno nem do diagrama completo; por isso, trata MSd e VSd como grandezas de entrada e não tenta reconstruir reações ou flechas.",
        "Rastreabilidade e limites",
        "A auditabilidade depende da identificação da origem dos esforços, do modelo estrutural empregado, das combinações e dos efeitos considerados. Como não há campo de deslocamentos nem reações, as verificações de ELS e de forças transversais localizadas permanecem explicitamente fora do cálculo automático.",
    ),
    "Largura de influência e conversão de ações de área": (
        "Fundamento físico",
        "A largura de influência é a faixa de laje cuja carga é transferida para a viga analisada. Em um modelo tributário usual, cada painel adjacente contribui até a linha média entre a viga e o apoio paralelo seguinte; por isso, as larguras declaradas à esquerda e à direita entram pela metade na largura total B.",
        "Conversão e interpretação",
        "Uma ação superficial, expressa em kN/m², é convertida em ação linear pela multiplicação por B, em metros. A operação conserva a resultante do carregamento na faixa tributária. Este procedimento pressupõe distribuição compatível com o modelo de piso adotado e não substitui uma análise bidimensional quando houver redistribuição significativa, balanços de laje ou rigidez transversal relevante.",
    ),
    "Combinação última normal": (
        "Finalidade do ELU",
        "A combinação última transforma ações características em ações de cálculo para verificar segurança contra escoamento, instabilidade e ruptura. Cada parcela é ponderada conforme sua natureza e sua possibilidade de atuar desfavoravelmente, mantendo separadas as ações permanentes, o peso próprio do perfil e a ação variável principal.",
        "Composição e leitura",
        "A soma é feita sobre ações compatíveis e simultâneas. O peso próprio provém da massa linear do perfil e é convertido em força distribuída antes da ponderação. Os coeficientes exibidos pertencem à combinação declarada; qualquer mudança de categoria, ação excepcional, vento, equipamento ou simultaneidade exige a combinação normativa correspondente, e não apenas a troca de um número isolado.",
    ),
    "Reações e momentos de extremidade": (
        "Equilíbrio e compatibilidade",
        "As reações são as forças e momentos que os vínculos precisam desenvolver para equilibrar as ações aplicadas. Em sistemas isostáticos, as equações de equilíbrio determinam diretamente as incógnitas. Em vínculos hiperestáticos, como engastes e vigas engastadas-apoiadas, também se impõem condições de rotação ou deslocamento para obter uma solução compatível.",
        "Hipóteses do modelo",
        "As expressões adotam viga prismática, comportamento elástico linear, pequenas deformações e rigidez EI constante. A posição a localiza a força pontual e b = L − a completa o vão. Os sinais dos momentos de extremidade seguem a convenção interna do modelo e são preservados na construção dos diagramas.",
    ),
    "Funções de cortante e momento": (
        "Relações diferenciais",
        "O cortante e o momento são funções da coordenada longitudinal. Para uma viga, dM/dx = V e dV/dx = −q; uma força concentrada provoca salto no diagrama de cortante e mudança de inclinação no diagrama de momento. As funções de singularidade permitem escrever essas contribuições em uma única expressão válida antes e depois da carga pontual.",
        "Busca dos valores críticos",
        "O máximo momento ocorre nas extremidades, em descontinuidades relevantes ou onde V(x) = 0. O máximo cortante é pesquisado imediatamente antes e depois das forças concentradas e nos extremos. Cada estado-limite usa o maior valor absoluto de sua própria função; máximos que pertencem a seções diferentes não são somados artificialmente.",
    ),
    "Gradiente de momento no trecho destravado": (
        "Significado de Cb",
        "Cb representa a influência da forma do diagrama de momento sobre a flambagem lateral com torção. Um trecho submetido a momento quase uniforme é mais desfavorável que outro em que apenas uma pequena região se aproxima do máximo, pois uma extensão maior da mesa comprimida participa da instabilidade.",
        "Avaliação do trecho",
        "Os momentos são tomados em módulo no máximo e nos quartos do comprimento destravado Lb. O trecho deve coincidir com as contenções laterais efetivas da mesa comprimida. O fator modifica o momento crítico, mas não corrige um Lb escolhido incorretamente nem substitui a verificação das contenções e de sua rigidez.",
    ),
    "Fator de modificação Cb informado": (
        "Origem do parâmetro",
        "Quando Cb é informado, ele representa uma propriedade do diagrama de momento no trecho destravado e deve vir de uma análise compatível com a vinculação, as ações e a posição das contenções. Não é uma propriedade geométrica fixa do perfil.",
        "Responsabilidade de uso",
        "O memorial registra simultaneamente Cb e Lb porque os dois parâmetros atuam juntos na FLT. A justificativa deve indicar o trecho, os momentos utilizados e a referência do cálculo. Alterações no carregamento ou nas contenções podem invalidar o valor mesmo que o perfil permaneça o mesmo.",
    ),
    "Momento plástico e limite geral": (
        "Plastificação da seção",
        "Mpl = Zx·fy corresponde à distribuição plástica idealizada de tensões no eixo forte, com tração e compressão atingindo fy. Zx mede a capacidade geométrica da seção totalmente plastificada e difere do módulo elástico Wx, associado ao início do escoamento da fibra extrema.",
        "Limitação resistente",
        "A resistência dos estados-limites de flexão não pode superar o limite geral expresso em função de Wx e fy. Esse teto impede que fatores favoráveis de estabilidade ou interpolações produzam resistência incompatível com a regra normativa. A divisão por γa1 transforma o valor nominal em resistência de cálculo.",
    ),
    "Classificação da alma à flexão": (
        "Esbeltez local",
        "A razão h/tw mede a propensão da alma comprimida a perder estabilidade local antes da formação da resistência plástica. λp separa o comportamento compacto do semicompacto, enquanto λr marca a transição para alma esbelta. Os limites dependem de E/fy porque a flambagem elástica é governada pela rigidez e pelo nível de tensão.",
        "Consequência da classificação",
        "Almas compactas podem participar da plastificação prevista no procedimento geral; almas entre λp e λr exigem transição inelástica. Quando h/tw ultrapassa λr, o procedimento do Anexo E passa a controlar os perfis soldados dentro de seus limites de aplicabilidade, com redução associada à alma esbelta.",
    ),
    "Flambagem lateral com torção — FLT": (
        "Mecanismo de instabilidade",
        "Na FLT, a mesa comprimida tende a deslocar-se lateralmente e a seção gira, combinando flexão no eixo de menor inércia, torção de Saint-Venant e empenamento. Iy, J e Cw representam essas parcelas de rigidez, enquanto Lb define o comprimento livre para o modo de instabilidade e Cb incorpora o gradiente de momento.",
        "Regimes resistente",
        "Mcr é o momento crítico elástico do trecho. A esbeltez reduzida compara Mpl a Mcr e seleciona o ramo plástico, inelástico ou elástico de χLT. No ramo inelástico há escoamento parcial antes da instabilidade; no elástico, a perda de estabilidade ocorre com tensões predominantemente abaixo de fy. A resistência final também respeita γa1 e o limite geral.",
    ),
    "Anexo E — alma esbelta e FLT": (
        "Efeito da alma esbelta",
        "Uma alma esbelta não consegue manter integralmente a distribuição de tensões assumida para uma seção não esbelta. O fator kpg reduz os momentos de referência conforme a razão entre a área da alma comprimida e a área da mesa, a esbeltez h/tw e o limite elástico associado ao material.",
        "Modelo da mesa comprimida",
        "A FLT é avaliada com a mesa comprimida associada a uma faixa de alma igual a hc/6. Dessa área resultam Iyc, Ayc e ryc; a razão Lb/ryc define λLT. Os limites λp e λr separam plastificação, transição inelástica e flambagem elástica. O Anexo E somente é aplicável quando fabricação, geometria, ar e h/tw atendem aos limites declarados.",
    ),
    "Flambagem local da mesa comprimida — FLM": (
        "Comportamento da mesa",
        "Cada metade da mesa comprimida funciona como uma placa em balanço ligada à alma. A esbeltez bf/(2·tf) expressa a relação entre largura livre e espessura. Quanto maior essa razão, menor a tensão necessária para ocorrer ondulação local da mesa antes que toda a seção desenvolva sua resistência.",
        "Coeficiente kc e transição entre regimes",
        "Nos perfis soldados, calcula-se primeiro kc,0 = 4/√(h/tw). O limite superior impede kc de ultrapassar 0,76; em seguida, o limite inferior impede valor menor que 0,35. Portanto: se kc,0 > 0,76, adota-se 0,76; se 0,35 ≤ kc,0 ≤ 0,76, conserva-se kc,0; e se kc,0 < 0,35, adota-se 0,35. Até λp, a mesa é compacta; entre λp e λr, a resistência é interpolada; acima de λr governa Mcr.",
    ),
    "Alma à flexão ou escoamento da mesa tracionada": (
        "Alma não esbelta",
        "Para alma compacta, a seção pode alcançar o momento plástico previsto; para alma semicompacta, a resistência é interpolada entre Mpl e Mr conforme h/tw avança de λp a λr. Essa transição representa a redução de capacidade causada pela instabilidade local antes da plastificação completa.",
        "Alma esbelta",
        "No procedimento do Anexo E, a verificação correspondente limita o momento pelo escoamento da mesa tracionada, calculado com fy·Wx. O valor é dividido por γa1 e comparado ao limite geral. Assim, a mesa tracionada pode controlar mesmo quando as verificações da mesa comprimida e da FLT produzirem valores maiores.",
    ),
    "Furos na mesa tracionada": (
        "Perda de área líquida",
        "Furos para parafusos removem material da mesa tracionada e concentram deformações. A área líquida Afn é comparada à área bruta Afg por meio das forças de ruptura e escoamento. Yt ajusta a comparação conforme a relação entre fy e fu do aço.",
        "Limite por ruptura",
        "Se fu·Afn não alcançar Yt·fy·Afg, a ruptura da seção líquida pode preceder o comportamento dúctil esperado e passa a limitar o momento. A resistência usa a fração Afn/Afg, Wx, fu e γa2. Diâmetros de furos, disposição, escalonamento e área líquida devem representar o detalhamento real da ligação.",
    ),
    "Resistência governante à flexão": (
        "Princípio do mínimo",
        "Os estados-limites de flexão descrevem mecanismos físicos distintos que podem ocorrer antes dos demais. A resistência disponível é, portanto, o menor valor aplicável entre FLT, FLM, alma ou mesa tracionada, eventual ruptura na seção líquida e o limite geral.",
        "Interpretação do resultado",
        "O mecanismo que fornece o mínimo é o estado-limite governante para os dados analisados. Isso não elimina as demais verificações: mudanças em Lb, espessuras, fabricação, furos ou material podem alterar o mecanismo crítico. Uma pendência de aplicabilidade impede que um número aparentemente favorável seja tratado como verificação completa.",
    ),
    "Esbeltez da alma e coeficiente kv": (
        "Flambagem por cisalhamento",
        "A alma submetida a cisalhamento desenvolve tensões principais inclinadas e pode flambar como uma placa. A esbeltez h/tw mede sua suscetibilidade, e kv representa as condições de contorno e a relação de aspecto dos painéis delimitados por mesas e enrijecedores.",
        "Efeito dos enrijecedores",
        "Sem enrijecedor eficaz, adota-se o coeficiente correspondente ao painel não enrijecido. Enrijecedores só aumentam kv quando geometria, soldagem, esbeltez e inércia são efetivamente atendidas; a simples informação de um espaçamento não cria contenção. A razão a/h controla quanto o painel é subdividido.",
    ),
    "Validação dos enrijecedores transversais": (
        "Função estrutural",
        "O enrijecedor transversal precisa restringir a deformação fora do plano da alma e transmitir as ações associadas sem instabilizar. Sua eficiência depende da ligação à alma e às mesas, da esbeltez da chapa e da rigidez à flexão em torno do eixo situado no plano médio da alma.",
        "Critérios verificados",
        "A expressão de j, incluindo a correção da Errata 1:2025, define a inércia mínima Ireq = a·tw³·j. A inércia fornecida Ist considera as chapas reais e o afastamento ao plano médio da alma. O limite b/t evita flambagem local do próprio enrijecedor. Somente a aprovação conjunta dos critérios permite usar o kv do painel enrijecido.",
    ),
    "Resistência da alma ao cisalhamento": (
        "Resistência plástica",
        "Vpl representa o escoamento por cisalhamento da área da alma, adotando tensão de referência igual a 0,60·fy. Os limites λp e λr, calculados com kv, E e fy, identificam se a alma escoa antes de flambar ou se a instabilidade reduz a capacidade.",
        "Equações por regime",
        "Para λ ≤ λp, governa o escoamento. Entre λp e λr, a flambagem é inelástica e a resistência decresce proporcionalmente a λp/λ. Acima de λr, o ramo elástico varia com o quadrado dessa razão. Em todos os casos, γa1 converte a resistência nominal em resistência de cálculo.",
    ),
    "Escoamento local da alma": (
        "Mecanismo resistente",
        "Uma reação ou força concentrada comprime a alma junto à mesa carregada. A carga se dispersa por uma faixa efetiva formada pelo comprimento de atuação ℓn e por múltiplos da dimensão k, que inclui a espessura da mesa e o raio de concordância ou a raiz de solda.",
        "Posição da força",
        "Longe da extremidade, há maior comprimento disponível para dispersão e utiliza-se o caso interno. Próximo à extremidade, a propagação de tensões é truncada e a faixa resistente diminui. A força de cálculo resulta da área efetiva da alma multiplicada por fy e dividida por γa1.",
    ),
    "Enrugamento da alma": (
        "Natureza do estado-limite",
        "O enrugamento combina deformação local, flexão e instabilidade da alma sob compressão transversal. Diferentemente do escoamento local puro, sua resistência depende de E, das relações entre tw e tf, do comprimento carregado e da proximidade da extremidade.",
        "Casos geométricos",
        "O coeficiente básico e o termo de amplificação mudam entre seção interna e extremidade. Na extremidade, a razão ℓn/d separa duas expressões porque o comprimento de distribuição da força é limitado. A raiz quadrada de E·fy·tf/tw representa a interação entre rigidez elástica, resistência do material e contenção fornecida pela mesa.",
    ),
    "Flambagem lateral da alma": (
        "Mecanismo e aplicabilidade",
        "A força transversal pode provocar deslocamento lateral da mesa comprimida em relação à mesa tracionada, acompanhado de flexão lateral da alma. O fenômeno somente é aplicável quando esse movimento relativo não está impedido e quando o índice geométrico η permanece dentro do limite correspondente à contenção de rotação da mesa.",
        "Resistência quando aplicável",
        "Cr depende do momento local em relação a Mr, pois a proximidade do escoamento reduz a rigidez disponível. A resistência combina Cr, tw³, tf, h e um termo cúbico de η. Para almas esbeltas soldadas, kpg reduz Mr. A condição de rotação impedida acrescenta uma parcela resistente que não existe no caso livre.",
    ),
    "Flambagem lateral da alma — critério geométrico": (
        "Triagem geométrica",
        "Antes de calcular uma resistência, compara-se η = (h/tw)/(ℓ/bf) ao limite normativo. Esse índice relaciona a esbeltez da alma com o comprimento disponível para deslocamento lateral da mesa. Valores acima do limite indicam que o modo de flambagem lateral da alma não se desenvolve segundo o critério analisado.",
        "Consequência",
        "Quando a triagem indica que o fenômeno não ocorre, nenhuma resistência artificial é incluída no mínimo governante. O resultado é registrado como não aplicável, mantendo separadas a ausência física do modo de falha e uma eventual falta de dados para calculá-lo.",
    ),
    "Flambagem lateral da alma — aplicabilidade": (
        "Condição de contenção",
        "Este estado-limite pressupõe movimento lateral relativo entre as mesas. Se apoios, contraventamentos ou outros elementos impedem esse movimento, o modo cinemático necessário à flambagem lateral da alma deixa de existir no modelo declarado.",
        "Registro no memorial",
        "A verificação é marcada como não aplicável, e não como resistência infinita ou aprovação numérica. A contenção declarada precisa existir no detalhamento, possuir rigidez e resistência compatíveis e manter-se efetiva durante todas as fases relevantes da estrutura.",
    ),
    "Resistência local governante": (
        "Combinação de mecanismos",
        "Escoamento local, enrugamento e flambagem lateral da alma são alternativas de falha sob a mesma força transversal localizada. Como qualquer uma pode ocorrer primeiro, a resistência disponível é o menor valor entre os mecanismos aplicáveis.",
        "Uso no projeto",
        "A demanda da reação ou carga pontual é comparada diretamente a esse mínimo. Se a resistência for insuficiente, a solução exige revisão de geometria, aumento do comprimento de apoio ou dimensionamento e detalhamento de enrijecedores locais e soldas; não basta substituir o mínimo por um mecanismo mais favorável.",
    ),
    "Combinação de serviço": (
        "Finalidade do ELS",
        "O estado-limite de serviço avalia desempenho, aparência e compatibilidade com elementos não estruturais sob níveis de ação representativos do uso. Por isso, utiliza fatores ψ de combinação e não os coeficientes de majoração do ELU.",
        "Seleção da combinação",
        "A combinação rara, frequente ou quase permanente representa durações e probabilidades distintas. As ações permanentes permanecem quando a combinação as inclui, enquanto a variável é multiplicada pelo fator declarado. A escolha deve corresponder ao fenômeno verificado; copiar a combinação resistente para a flecha produziria uma interpretação física incorreta.",
    ),
    "Linha elástica por funções de singularidade": (
        "Integração da curvatura",
        "No regime elástico linear, a curvatura é relacionada ao momento por E·Ix·v''(x) = M(x). Duas integrações fornecem rotação e deslocamento. As funções de singularidade mantêm a expressão válida em todo o vão mesmo com força pontual, e as constantes de integração são determinadas pelas condições de contorno da vinculação.",
        "Localização da flecha máxima",
        "A flecha é calculada com sinais e o valor máximo é escolhido em módulo ao longo da viga, incluindo a posição da força concentrada. E e Ix devem representar a rigidez efetiva compatível com o modelo. O procedimento não inclui automaticamente fluência, fissuração de elementos mistos, deformações de ligações ou contraflecha.",
    ),
    "Deslocamento limite": (
        "Critério funcional",
        "O limite relativo Lref/n controla deformações que podem prejudicar pisos, revestimentos, equipamentos e percepção dos usuários. O divisor n depende da categoria de uso. Para balanços, Lref é o dobro do comprimento teórico, conforme a convenção normativa aplicável ao limite.",
        "Limites simultâneos",
        "Quando existe alvenaria solidarizada, o limite absoluto adicional de 15 mm é comparado ao limite relativo, e o menor governa. A verificação trata o deslocamento calculado para a combinação de serviço declarada; requisitos específicos de fachadas, drenagem, vibração ou equipamentos podem impor critérios adicionais.",
    ),
}


def _step_theory_panel(title, reference):
    theory = _STEP_THEORY.get(title)
    if theory is None:
        raise ValueError(f"Fundamentação teórica específica não cadastrada para a etapa: {title}")
    heading_a, text_a, heading_b, text_b = theory
    return f"""
    <details class="step-theory-panel">
      <summary><span>Teoria da análise</span><strong>{_esc(title)}</strong></summary>
      <div class="step-theory-content">
        <section><h5>{_esc(heading_a)}</h5><p>{_esc(text_a)}</p></section>
        <section><h5>{_esc(heading_b)}</h5><p>{_esc(text_b)}</p></section>
        <div class="norm-ref">Base normativa desta etapa: {_esc(reference)}</div>
      </div>
    </details>"""


def _step(number, title, explanation, symbolic, numeric, result, reference, decision=None, equation_title=None):
    decision_html = ""
    if decision:
        decision_html = f'<div class="calc-decision"><strong>Leitura técnica:</strong> {_esc(decision)}</div>'
    heading = _equation_heading(title, decision, equation_title)
    heading_html = f'<div class="equation-heading"><h5>{_esc(heading)}</h5></div>' if heading else ""
    equation_chain = _equation_chain(symbolic, numeric)
    theory_panel = _step_theory_panel(title, reference)
    return f"""
    <article class="calc-step">
      <div class="calc-step-head"><span class="calc-step-number">{number}</span><h4>{_esc(title)}</h4></div>
      <p class="calc-explanation">{_esc(explanation)}</p>
      {theory_panel}
      {heading_html}
      <div class="formula-chain">{equation_chain}</div>
      <div class="calc-result">{result}</div>
      {decision_html}
      <div class="norm-ref">Referência: {_esc(reference)}</div>
    </article>"""


def _verification(title, demand, resistance, unit, status, efficiency, demand_symbol="S_d", resistance_symbol="R_d", reference=""):
    cls = _status_class(status)
    comparison = "\\le" if demand <= resistance else ">"
    return f"""
    <div class="verification-card {cls}">
      <div><span class="verification-kicker">VERIFICAÇÃO</span><h4>{_esc(title)}</h4></div>
      <div class="verification-chain">
        <div class="equation-line equation-symbolic">$${demand_symbol} {comparison} {resistance_symbol}$$</div>
        <div class="equation-line equation-numeric">$${_n(demand)}\\;{unit}\\; {comparison}\\; {_n(resistance)}\\;{unit}$$</div>
      </div>
      <div class="verification-metrics"><span>Utilização: <strong>{_n(efficiency, 1)}%</strong></span><span class="{cls}">{_esc(status)}</span></div>
      {f'<div class="norm-ref">Referência: {_esc(reference)}</div>' if reference else ''}
    </div>"""


def _chapter(title, intro):
    return f'<h2>{_esc(title)}</h2><p class="chapter-intro">{_esc(intro)}</p>'


def _beam_actions(bundle):
    response = bundle.get("elu_response")
    loads = bundle.get("elu_loads")
    if not response or not loads:
        return _chapter("3. Modelo, ações e esforços solicitantes", "Entrada manual de esforços já combinados.") + _beam_theory() + _step(
            "3.1", "Esforços informados", "O aplicativo utiliza diretamente os esforços de cálculo informados. Sem ações e reações não é possível reconstruir os diagramas nem auditar ELS e forças localizadas.",
            _eq(r"M_{Sd}=M_{Sd,informado}", r"V_{Sd}=V_{Sd,informado}"),
            _eq(rf"M_{{Sd}}={_n(bundle['Msd']/100)}\;kN\!\cdot\!m", rf"V_{{Sd}}={_n(bundle['Vsd'])}\;kN"),
            f"Momento de cálculo: <strong>{_n(bundle['Msd']/100)} kN·m</strong>; cortante de cálculo: <strong>{_n(bundle['Vsd'])} kN</strong>.",
            "Responsabilidade do usuário pela combinação e pela análise global.",
            "O memorial identifica explicitamente a limitação; nenhum diagrama é inventado.",
        )

    qg, qq, qpp = loads["q_permanent"], loads["q_variable"], loads["self_weight"]
    pg, pq = loads["point_permanent"], loads["point_variable"]
    influence = ""
    if bundle.get("influence_width_m") is not None:
        influence = _step(
            "3.1", "Largura de influência e conversão de ações de área",
            "Cada lado da laje contribui com metade de sua largura. As ações de área são multiplicadas pela largura de influência para obter ações lineares características.",
            _eq(
                r"B=\frac{b_{esq}+b_{dir}}{2}",
                r"q_{G,k}=g_k\cdot B",
                r"q_{Q,k}=q_k\cdot B",
            ),
            _eq(
                rf"B=\frac{{{_n(bundle['influence_left_cm']/100)}+{_n(bundle['influence_right_cm']/100)}}}{{2}}={_n(bundle['influence_width_m'])}\;m",
                rf"q_{{G,k}}={_n(bundle.get('g_area'))}\cdot{_n(bundle['influence_width_m'])}={_n(qg*100)}\;kN/m",
                rf"q_{{Q,k}}={_n(bundle.get('q_area'))}\cdot{_n(bundle['influence_width_m'])}={_n(qq*100)}\;kN/m",
            ),
            f"qG,k = <strong>{_n(qg*100)} kN/m</strong>; qQ,k = <strong>{_n(qq*100)} kN/m</strong>.",
            "Modelo de distribuição informado pelo usuário; valores característicos conforme as normas de ações aplicáveis.",
        )
    step_combo = _step(
        "3.2", "Combinação última normal",
        "As parcelas permanentes, o peso próprio específico do perfil e a ação variável principal são majorados separadamente. O peso próprio é obtido da massa linear da tabela do perfil.",
        _eq(
            r"q_d=\gamma_g\cdot q_{G,k}+\gamma_{pp}\cdot q_{pp,k}+\gamma_q\cdot q_{Q,k}",
            r"P_d=\gamma_g\cdot P_{G,k}+\gamma_q\cdot P_{Q,k}",
        ),
        _eq(
            rf"q_d={_n(loads['gamma_g'],2)}\cdot{_n(qg*100)}+{_n(loads['gamma_self_weight'],2)}\cdot{_n(qpp*100)}+{_n(loads['gamma_q'],2)}\cdot{_n(qq*100)}={_n(loads['q']*100)}\;kN/m",
            rf"P_d={_n(loads['gamma_g'],2)}\cdot{_n(pg)}+{_n(loads['gamma_q'],2)}\cdot{_n(pq)}={_n(loads['P'])}\;kN",
        ),
        f"Ações de cálculo: <strong>qd = {_n(loads['q']*100)} kN/m</strong> e <strong>Pd = {_n(loads['P'])} kN</strong>.",
        loads["reference"], bundle.get("elu_combination_text"),
    )
    L, q, P, a = response.length, response.q, response.point_load, response.point_position
    support_formulas = {
        "simply_supported": _eq(
            r"R_A=\frac{q\cdot L}{2}+\frac{P\cdot(L-a)}{L}",
            r"R_B=\frac{q\cdot L}{2}+\frac{P\cdot a}{L}",
            r"M_A=0",
            r"M_B=0",
        ),
        "cantilever": _eq(
            r"R_A=q\cdot L+P", r"R_B=0",
            r"M_A=-\left(\frac{q\cdot L^2}{2}+P\cdot a\right)", r"M_B=0",
        ),
        "fixed_fixed": _eq(
            r"b=L-a",
            r"R_A=\frac{q\cdot L}{2}+\frac{P\cdot b^2\cdot(3\cdot a+b)}{L^3}",
            r"R_B=q\cdot L+P-R_A",
            r"M_A=-\frac{q\cdot L^2}{12}-\frac{P\cdot a\cdot b^2}{L^2}",
        ),
        "propped_cantilever": _eq(
            r"R_B=\frac{3\cdot q\cdot L}{8}+\frac{P\cdot a^2\cdot(3\cdot L-a)}{2\cdot L^3}",
            r"R_A=q\cdot L+P-R_B",
            r"M_A=R_B\cdot L-\frac{q\cdot L^2}{2}-P\cdot a",
        ),
    }
    # As equações de vigas são apresentadas em kN e m para que cada igualdade
    # mantenha coerência dimensional também nos momentos (kN·m).
    L_m, a_m, q_m = L / 100.0, a / 100.0, q * 100.0
    b_m = L_m - a_m
    support_numeric = {
        "simply_supported": _eq(
            rf"R_A=\frac{{{_n(q_m,6)}\cdot{_n(L_m)}}}{{2}}+\frac{{{_n(P)}\cdot({_n(L_m)}-{_n(a_m)})}}{{{_n(L_m)}}}={_n(response.reaction_left)}\;kN",
            rf"R_B=\frac{{{_n(q_m,6)}\cdot{_n(L_m)}}}{{2}}+\frac{{{_n(P)}\cdot{_n(a_m)}}}{{{_n(L_m)}}}={_n(response.reaction_right)}\;kN",
            rf"M_A=0={_n(response.moment_left/100)}\;kN\!\cdot\!m",
            rf"M_B=0={_n(response.moment_right/100)}\;kN\!\cdot\!m",
        ),
        "cantilever": _eq(
            rf"R_A={_n(q_m,6)}\cdot{_n(L_m)}+{_n(P)}={_n(response.reaction_left)}\;kN",
            rf"R_B=0={_n(response.reaction_right)}\;kN",
            rf"M_A=-\left(\frac{{{_n(q_m,6)}\cdot{_n(L_m)}^2}}{{2}}+{_n(P)}\cdot{_n(a_m)}\right)={_n(response.moment_left/100)}\;kN\!\cdot\!m",
            rf"M_B=0={_n(response.moment_right/100)}\;kN\!\cdot\!m",
        ),
        "fixed_fixed": _eq(
            rf"b={_n(L_m)}-{_n(a_m)}={_n(b_m)}\;m",
            rf"R_A=\frac{{{_n(q_m,6)}\cdot{_n(L_m)}}}{{2}}+\frac{{{_n(P)}\cdot{_n(b_m)}^2\cdot(3\cdot{_n(a_m)}+{_n(b_m)})}}{{{_n(L_m)}^3}}={_n(response.reaction_left)}\;kN",
            rf"R_B={_n(q_m,6)}\cdot{_n(L_m)}+{_n(P)}-{_n(response.reaction_left)}={_n(response.reaction_right)}\;kN",
            rf"M_A=-\frac{{{_n(q_m,6)}\cdot{_n(L_m)}^2}}{{12}}-\frac{{{_n(P)}\cdot{_n(a_m)}\cdot{_n(b_m)}^2}}{{{_n(L_m)}^2}}={_n(response.moment_left/100)}\;kN\!\cdot\!m",
        ),
        "propped_cantilever": _eq(
            rf"R_B=\frac{{3\cdot{_n(q_m,6)}\cdot{_n(L_m)}}}{{8}}+\frac{{{_n(P)}\cdot{_n(a_m)}^2\cdot(3\cdot{_n(L_m)}-{_n(a_m)})}}{{2\cdot{_n(L_m)}^3}}={_n(response.reaction_right)}\;kN",
            rf"R_A={_n(q_m,6)}\cdot{_n(L_m)}+{_n(P)}-{_n(response.reaction_right)}={_n(response.reaction_left)}\;kN",
            rf"M_A={_n(response.reaction_right)}\cdot{_n(L_m)}-\frac{{{_n(q_m,6)}\cdot{_n(L_m)}^2}}{{2}}-{_n(P)}\cdot{_n(a_m)}={_n(response.moment_left/100)}\;kN\!\cdot\!m",
        ),
    }
    step_reactions = _step(
        "3.3", "Reações e momentos de extremidade",
        "As condições de contorno da vinculação selecionada são aplicadas à viga prismática. Para b = L − a, as expressões abaixo produzem as ações de extremidade usadas nos diagramas.",
        support_formulas[response.support],
        support_numeric[response.support],
        f"RA = <strong>{_n(response.reaction_left)} kN</strong>; RB = <strong>{_n(response.reaction_right)} kN</strong>.",
        "Análise elástica de primeira ordem; equilíbrio e compatibilidade da vinculação idealizada.",
        None,
        "Equações de equilíbrio e compatibilidade — reações e momentos de extremidade",
    )
    x_m = response.max_moment_position
    m_signed = response.moment_at(x_m)
    v_index = max(range(len(response.shears)), key=lambda idx: abs(response.shears[idx]))
    x_v = response.x[v_index]
    v_signed = response.shears[v_index]
    x_m_plot, x_v_plot = x_m / 100.0, x_v / 100.0
    m_point_term = max(x_m_plot - a_m, 0.0)
    h_v = 1.0 if x_v >= a and P > 0 else 0.0
    step_diagrams = _step(
        "3.4", "Funções de cortante e momento",
        "A carga distribuída e a força pontual são analisadas simultaneamente por funções de singularidade. Os extremos de momento são pesquisados nas extremidades, em x = a e nas raízes V(x) = 0; não se somam máximos que ocorram em seções diferentes.",
        _eq(
            r"M(x)=M_A+R_A\cdot x-\frac{q_d\cdot x^2}{2}-P_d\cdot\langle x-a\rangle",
            r"M_{Sd,max}=\max_x\left|M(x)\right|",
            r"V(x)=R_A-q_d\cdot x-P_d\cdot H(x-a)",
            r"V_{Sd,max}=\max_x\left|V(x)\right|",
        ),
        _eq(
            rf"M({_n(x_m_plot)})={_n(response.moment_left/100)}+{_n(response.reaction_left)}\cdot{_n(x_m_plot)}-\frac{{{_n(q_m,6)}\cdot{_n(x_m_plot)}^2}}{{2}}-{_n(P)}\cdot{_n(m_point_term)}={_n(m_signed/100)}\;kN\!\cdot\!m",
            rf"M_{{Sd,max}}={_n(response.max_moment/100)}\;kN\!\cdot\!m",
            rf"V({_n(x_v_plot)})={_n(response.reaction_left)}-{_n(q_m,6)}\cdot{_n(x_v_plot)}-{_n(P)}\cdot{_n(h_v,0)}={_n(v_signed)}\;kN",
            rf"V_{{Sd,max}}={_n(response.max_shear)}\;kN",
        ),
        f"Solicitações adotadas: <strong>MSd = {_n(response.max_moment/100)} kN·m</strong> e <strong>VSd = {_n(response.max_shear)} kN</strong>.",
        "Modelo de análise do aplicativo; sinais internos em kN e cm.",
        "O valor absoluto máximo governa cada verificação de resistência.",
        "Equações dos esforços internos — avaliação nas seções críticas",
    )
    return _chapter("3. Modelo, ações e esforços solicitantes", "Rastreabilidade completa desde as ações características até os esforços de cálculo.") + _beam_theory() + influence + step_combo + step_reactions + step_diagrams


def _cb_section(bundle):
    info = bundle.get("cb_info")
    if info:
        body = _step(
            "4.1", "Gradiente de momento no trecho destravado",
            "Os momentos são avaliados em módulo nos quartos do trecho Lb. Para seção I duplamente simétrica usa-se Rm = 1,0.",
            _eq(r"C_{b,calc}=\frac{12{,}5\cdot M_{max}}{2{,}5\cdot M_{max}+3\cdot M_A+4\cdot M_B+3\cdot M_C}", r"C_b=\min(C_{b,calc};3{,}0)"),
            _eq(
                rf"C_{{b,calc}}=\frac{{12.5\cdot{_n(info['Mmax']/100)}}}{{2.5\cdot{_n(info['Mmax']/100)}+3\cdot{_n(info['MA']/100)}+4\cdot{_n(info['MB']/100)}+3\cdot{_n(info['MC']/100)}}}={_n(info['Cb'],4)}",
                rf"C_b=\min({_n(info['Cb'],4)};3.0)={_n(min(info['Cb'],3.0),4)}",
            ),
            f"Trecho x = {_n(info['segment_start']/100)} m a {_n((info['segment_start']+info['Lb'])/100)} m; <strong>Cb = {_n(info['Cb'],4)}</strong>.",
            info["reference"],
            f"MA = {_n(info['MA']/100)}; MB = {_n(info['MB']/100)}; MC = {_n(info['MC']/100)}; Mmax = {_n(info['Mmax']/100)} kN·m.",
        )
    else:
        body = _step(
            "4.1", "Fator de modificação Cb informado",
            "O cálculo de estabilidade usa o valor fornecido e registra sua origem. Quando não há análise automática, a justificativa do Cb integra os dados de projeto.",
            _eq(r"C_b=C_{b,informado}", r"L_b=L_{b,informado}"),
            _eq(rf"C_b={_n(bundle['Cb'],4)}", rf"L_b={_n(bundle['Lb']/100)}\;m"),
            f"Valor adotado: <strong>Cb = {_n(bundle['Cb'],4)}</strong>; Lb = <strong>{_n(bundle['Lb']/100)} m</strong>.",
            "ABNT NBR 8800:2024, 5.4.2.3 a 5.4.2.5.", bundle.get("cb_basis"),
        )
    return _chapter("4. Trecho destravado e fator Cb", "O gradiente de momento é documentado antes da verificação da flambagem lateral com torção.") + _cb_theory() + body


def _flexure_section(bundle):
    f, p = bundle["flexure"], bundle["props"]
    fy, fu, E = bundle["fy"], bundle["fu"], bundle["E"]
    gamma1, gamma2, Msd = bundle["gamma_a1"], bundle["gamma_a2"], bundle["Msd"]
    out = _chapter("5. Resistência à flexão no eixo forte", "Cada estado-limite é desenvolvido separadamente; a menor resistência aplicável governa.") + _flexure_theory()
    out += _step(
        "5.1", "Momento plástico e limite geral",
        "Calculam-se o momento plástico nominal e o teto resistente da seção para evitar que qualquer estado-limite ultrapasse o limite geral da flexão.",
        _eq(r"M_{pl}=Z_x\cdot f_y", r"M_{Rd,lim}=\frac{1{,}50\cdot W_x\cdot f_y}{\gamma_{a1}}"),
        _eq(
            rf"M_{{pl}}=\frac{{{_n(p['Zx'])}\cdot{_n(fy)}}}{{100}}={_n(f['Mpl']/100)}\;kN\!\cdot\!m",
            rf"M_{{Rd,lim}}=\frac{{1.50\cdot{_n(p['Wx'])}\cdot{_n(fy)}}}{{100\cdot{_n(gamma1,2)}}}={_n(f['cap_5_4_2_2']/100)}\;kN\!\cdot\!m",
        ),
        f"Mpl = <strong>{_n(f['Mpl']/100)} kN·m</strong>; limite geral = <strong>{_n(f['cap_5_4_2_2']/100)} kN·m</strong>.",
        "ABNT NBR 8800:2024, 5.4.2.2.",
    )
    web_decision = "alma esbelta: aplicar Anexo E" if f["slender_web"] else ("alma compacta" if f["lambda_FLA"] <= f["lambda_p_FLA"] else "alma semicompacta")
    out += _step(
        "5.2", "Classificação da alma à flexão",
        "A esbeltez da alma é comparada aos limites plástico e elástico; essa decisão define se o procedimento geral do Anexo D ou o Anexo E deve ser usado.",
        _eq(
            r"\lambda_w=\frac{h}{t_w}",
            r"\lambda_p=3{,}76\cdot\sqrt{\frac{E}{f_y}}",
            r"\lambda_r=5{,}70\cdot\sqrt{\frac{E}{f_y}}",
        ),
        _eq(
            rf"\lambda_w=\frac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}={_n(f['lambda_FLA'])}",
            rf"\lambda_p=3.76\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}={_n(f['lambda_p_FLA'])}",
            rf"\lambda_r=5.70\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}={_n(f['lambda_r_FLA'])}",
        ),
        f"Classificação: <strong>{_esc(web_decision)}</strong>.",
        "ABNT NBR 8800:2024, Anexo D e Anexo E.", web_decision,
    )
    if not f["slender_web"]:
        chi_formula = r"\chi_{LT}=1" if f["lambda_LT"] <= .4 else (r"\chi_{LT}=1-0{,}49\cdot(\lambda_{LT}-0{,}4)" if f["lambda_LT"] <= 1.4 else r"\chi_{LT}=\frac{1}{\lambda_{LT}^2}")
        chi_numeric = (
            rf"\chi_{{LT}}=1={_n(f['chi_LT'],4)}"
            if f["lambda_LT"] <= .4
            else rf"\chi_{{LT}}=1-0.49\cdot({_n(f['lambda_LT'])}-0.4)={_n(f['chi_LT'],4)}"
            if f["lambda_LT"] <= 1.4
            else rf"\chi_{{LT}}=\frac{{1}}{{{_n(f['lambda_LT'])}^2}}={_n(f['chi_LT'],4)}"
        )
        out += _step(
            "5.3", "Flambagem lateral com torção — FLT",
            "Calcula-se o momento crítico elástico do trecho destravado, a esbeltez reduzida e o fator χLT correspondente ao intervalo identificado.",
            _eq(
                r"M_{cr}=\frac{C_b\cdot\pi^2\cdot E\cdot I_y}{L_b^2}\cdot\sqrt{\frac{C_w}{I_y}\cdot\left(1+0{,}039\cdot\frac{J\cdot L_b^2}{C_w}\right)}",
                r"\lambda_{LT}=\sqrt{\frac{M_{pl}}{M_{cr}}}", chi_formula,
                r"M_{Rd,FLT}=\min\left(\frac{\chi_{LT}\cdot M_{pl}}{\gamma_{a1}};\;M_{Rd,lim}\right)",
            ),
            _eq(
                rf"M_{{cr}}=\frac{{1}}{{100}}\cdot\frac{{{_n(bundle['Cb'],4)}\cdot\pi^2\cdot{_n(E)}\cdot{_n(p['Iy'])}}}{{{_n(bundle['Lb'])}^2}}\cdot\sqrt{{\frac{{{_n(p['Cw'])}}}{{{_n(p['Iy'])}}}\cdot\left(1+0.039\cdot\frac{{{_n(p['J'])}\cdot{_n(bundle['Lb'])}^2}}{{{_n(p['Cw'])}}}\right)}}={_n(f['Mcr_FLT']/100)}\;kN\!\cdot\!m",
                rf"\lambda_{{LT}}=\sqrt{{\frac{{{_n(f['Mpl']/100)}}}{{{_n(f['Mcr_FLT']/100)}}}}}={_n(f['lambda_LT'])}",
                chi_numeric,
                rf"M_{{Rd,FLT}}=\min\left(\frac{{{_n(f['chi_LT'],4)}\cdot{_n(f['Mpl']/100)}}}{{{_n(gamma1,2)}}};\;{_n(f['cap_5_4_2_2']/100)}\right)={_n((f['Mrd_FLT'] or 0)/100)}\;kN\!\cdot\!m",
            ),
            f"MRd,FLT = <strong>{'N/A' if f['Mrd_FLT'] is None else _n(f['Mrd_FLT']/100)+' kN·m'}</strong>; regime {f['regime_FLT']}.",
            "ABNT NBR 8800:2024, 5.4.2 e Anexo D, alternativa de D.2.1.", f["regime_FLT"],
        )
    else:
        out += _annex_e_step(bundle)
    welded = bundle["fabrication"].lower().startswith("sold")
    lr_formula = r"0{,}95\cdot\sqrt{\frac{E\cdot k_c}{f_y-\sigma_r}}" if welded else r"0{,}83\cdot\sqrt{\frac{E}{f_y-\sigma_r}}"
    mcr_formula = r"\frac{0{,}90\cdot E\cdot k_c\cdot W_x}{\lambda_f^2}" if welded else r"\frac{0{,}69\cdot E\cdot W_x}{\lambda_f^2}"
    if f["slender_web"]:
        mcr_formula = r"\frac{0{,}90\cdot k_{pg}\cdot E\cdot k_c\cdot W_{xc}}{\lambda_f^2}"
    if welded:
        flm_lr_numeric = rf"\lambda_r=0.95\cdot\sqrt{{\frac{{{_n(E)}\cdot{_n(f['kc'])}}}{{{_n(fy)}-{_n(f['sigma_r'])}}}}}={_n(f['lambda_r_FLM'])}"
    else:
        flm_lr_numeric = rf"\lambda_r=0.83\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}-{_n(f['sigma_r'])}}}}}={_n(f['lambda_r_FLM'])}"
    flm_base = f["M_y_annex_e"] if f["slender_web"] else f["Mpl"]
    flm_residual = f["M_r_annex_e"] if f["slender_web"] else f["Mr_FLM"]
    flm_base_symbol = r"M_y" if f["slender_web"] else r"M_{pl}"
    flm_base_formula = r"M_y=k_{pg}\cdot f_y\cdot W_{xc}" if f["slender_web"] else r"M_{pl}=Z_x\cdot f_y"
    flm_residual_formula = r"M_r=k_{pg}\cdot(f_y-\sigma_r)\cdot W_{xc}" if f["slender_web"] else r"M_r=(f_y-\sigma_r)\cdot W_x"
    if f["slender_web"]:
        flm_base_numeric = rf"M_y=\frac{{{_n(f['kpg'],4)}\cdot{_n(fy)}\cdot{_n(f['Wxc'])}}}{{100}}={_n(flm_base/100)}\;kN\!\cdot\!m"
        flm_residual_numeric = rf"M_r=\frac{{{_n(f['kpg'],4)}\cdot({_n(fy)}-{_n(f['sigma_r'])})\cdot{_n(f['Wxc'])}}}{{100}}={_n(flm_residual/100)}\;kN\!\cdot\!m"
        flm_mcr_numeric = rf"M_{{cr}}=\frac{{0.90\cdot{_n(f['kpg'],4)}\cdot{_n(E)}\cdot{_n(f['kc'])}\cdot{_n(f['Wxc'])}}}{{{_n(f['lambda_FLM'])}^2\cdot100}}={_n(f['Mcr_FLM']/100)}\;kN\!\cdot\!m"
    else:
        flm_base_numeric = rf"M_{{pl}}=\frac{{{_n(p['Zx'])}\cdot{_n(fy)}}}{{100}}={_n(flm_base/100)}\;kN\!\cdot\!m"
        flm_residual_numeric = rf"M_r=\frac{{({_n(fy)}-{_n(f['sigma_r'])})\cdot{_n(p['Wx'])}}}{{100}}={_n(flm_residual/100)}\;kN\!\cdot\!m"
        if welded:
            flm_mcr_numeric = rf"M_{{cr}}=\frac{{0.90\cdot{_n(E)}\cdot{_n(f['kc'])}\cdot{_n(p['Wx'])}}}{{{_n(f['lambda_FLM'])}^2\cdot100}}={_n(f['Mcr_FLM']/100)}\;kN\!\cdot\!m"
        else:
            flm_mcr_numeric = rf"M_{{cr}}=\frac{{0.69\cdot{_n(E)}\cdot{_n(p['Wx'])}}}{{{_n(f['lambda_FLM'])}^2\cdot100}}={_n(f['Mcr_FLM']/100)}\;kN\!\cdot\!m"
    kc_symbolic_lines = []
    kc_numeric_lines = []
    if welded:
        web_slenderness = p["h_clear"] / p["tw"]
        kc_unbounded = 4.0 / math.sqrt(web_slenderness)
        kc_upper_limited = min(kc_unbounded, 0.76)
        kc_symbolic_lines = [
            r"k_{c,0}=\frac{4}{\sqrt{\dfrac{h}{t_w}}}",
            r"k_{c,sup}=\min\left(k_{c,0};0{,}76\right)",
            r"k_c=\max\left(0{,}35;k_{c,sup}\right)",
        ]
        kc_numeric_lines = [
            rf"k_{{c,0}}=\frac{{4}}{{\sqrt{{\dfrac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}}}}}={_n(kc_unbounded,4)}",
            rf"k_{{c,sup}}=\min\left({_n(kc_unbounded,4)};0.7600\right)={_n(kc_upper_limited,4)}",
            rf"k_c=\max\left(0.3500;{_n(kc_upper_limited,4)}\right)={_n(f['kc'],4)}",
        ]
    if f["regime_FLM"] == "plástico":
        flm_active = rf"M_{{Rd,FLM}}=\min\left(\frac{{{flm_base_symbol}}}{{\gamma_{{a1}}}};M_{{Rd,lim}}\right)"
        flm_active_numeric = rf"M_{{Rd,FLM}}=\min\left(\frac{{{_n(flm_base/100)}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n(f['Mrd_FLM']/100)}\;kN\!\cdot\!m"
    elif f["regime_FLM"] == "inelástico":
        flm_active = rf"M_{{Rd,FLM}}=\min\left(\frac{{{flm_base_symbol}-({flm_base_symbol}-M_r)\cdot\dfrac{{\lambda_f-\lambda_p}}{{\lambda_r-\lambda_p}}}}{{\gamma_{{a1}}}};M_{{Rd,lim}}\right)"
        flm_active_numeric = rf"M_{{Rd,FLM}}=\min\left(\frac{{{_n(flm_base/100)}-({_n(flm_base/100)}-{_n(flm_residual/100)})\cdot\dfrac{{{_n(f['lambda_FLM'])}-{_n(f['lambda_p_FLM'])}}}{{{_n(f['lambda_r_FLM'])}-{_n(f['lambda_p_FLM'])}}}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n(f['Mrd_FLM']/100)}\;kN\!\cdot\!m"
    else:
        flm_active = r"M_{Rd,FLM}=\min\left(\frac{M_{cr}}{\gamma_{a1}};M_{Rd,lim}\right)"
        flm_active_numeric = rf"M_{{Rd,FLM}}=\min\left(\frac{{{_n(f['Mcr_FLM']/100)}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n(f['Mrd_FLM']/100)}\;kN\!\cdot\!m"
    out += _step(
        "5.4", "Flambagem local da mesa comprimida — FLM",
        "A esbeltez da meia mesa é comparada com λp e λr. O núcleo seleciona automaticamente a expressão plástica, interpolada inelástica ou crítica elástica.",
        _eq(
            r"\lambda_f=\frac{b_f}{2\cdot t_f}",
            *kc_symbolic_lines,
            r"\lambda_p=0{,}38\cdot\sqrt{\frac{E}{f_y}}",
            rf"\lambda_r={lr_formula}",
            flm_base_formula,
            flm_residual_formula,
            rf"M_{{cr}}={mcr_formula}", flm_active,
        ),
        _eq(
            rf"\lambda_f=\frac{{{_n(p['bf'])}}}{{2\cdot{_n(p['tf'])}}}={_n(f['lambda_FLM'])}",
            *kc_numeric_lines,
            rf"\lambda_p=0.38\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}={_n(f['lambda_p_FLM'])}",
            flm_lr_numeric,
            flm_base_numeric,
            flm_residual_numeric,
            flm_mcr_numeric,
            flm_active_numeric,
        ),
        f"MRd,FLM = <strong>{_n(f['Mrd_FLM']/100)} kN·m</strong>; regime {f['regime_FLM']}.",
        "ABNT NBR 8800:2024, 5.4.2, Anexo D ou Anexo E.", f["regime_FLM"],
    )
    if f["slender_web"]:
        fla_active = r"M_{Rd,t}=\min\left(\frac{f_y\cdot W_x}{\gamma_{a1}};M_{Rd,lim}\right)"
        fla_numeric = rf"M_{{Rd,t}}=\min\left(\frac{{{_n(fy)}\cdot{_n(p['Wx'])}}}{{100\cdot{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n(f['Mrd_FLA_or_tension']/100)}\;kN\!\cdot\!m"
        fla_title = "Equação de escoamento da mesa tracionada — Anexo E"
    elif f["regime_FLA"] == "plástico":
        fla_active = r"M_{Rd,FLA}=\min\left(\frac{M_{pl}}{\gamma_{a1}};M_{Rd,lim}\right)"
        fla_numeric = rf"M_{{Rd,FLA}}=\min\left(\frac{{{_n(f['Mpl']/100)}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n(f['Mrd_FLA_or_tension']/100)}\;kN\!\cdot\!m"
        fla_title = None
    else:
        fla_active = r"M_{Rd,FLA}=\min\left(\frac{M_{pl}-(M_{pl}-M_r)\cdot\dfrac{\lambda_w-\lambda_p}{\lambda_r-\lambda_p}}{\gamma_{a1}};M_{Rd,lim}\right)"
        fla_numeric = rf"M_{{Rd,FLA}}=\min\left(\frac{{{_n(f['Mpl']/100)}-({_n(f['Mpl']/100)}-{_n(f['Mr_FLA']/100)})\cdot\dfrac{{{_n(f['lambda_FLA'])}-{_n(f['lambda_p_FLA'])}}}{{{_n(f['lambda_r_FLA'])}-{_n(f['lambda_p_FLA'])}}}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n(f['Mrd_FLA_or_tension']/100)}\;kN\!\cdot\!m"
        fla_title = None
    out += _step(
        "5.5", "Alma à flexão ou escoamento da mesa tracionada",
        "Para alma não esbelta aplica-se o ramo plástico ou a interpolação até Mr = fyWx. No Anexo E verifica-se o escoamento da mesa tracionada.",
        _eq(r"\lambda_w=\frac{h}{t_w}", r"M_r=f_y\cdot W_x", fla_active),
        _eq(
            rf"\lambda_w=\frac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}={_n(f['lambda_FLA'])}",
            rf"M_r=\frac{{{_n(fy)}\cdot{_n(p['Wx'])}}}{{100}}={_n(fy*p['Wx']/100)}\;kN\!\cdot\!m",
            fla_numeric,
        ),
        f"Resistência = <strong>{_n(f['Mrd_FLA_or_tension']/100)} kN·m</strong>; {f['regime_FLA']}.",
        "ABNT NBR 8800:2024, Anexo D ou Anexo E.", f["regime_FLA"], fla_title,
    )
    if f.get("holes_checked"):
        Afg = f["Afg_tension"]
        Afn = f["Afn_tension"]
        Afn_over_Afg = Afn / Afg if Afg else math.nan
        rupture_display = (
            r"\mathrm{não\;limita}"
            if f["Mrd_rupture"] is None
            else rf"{_n(f['Mrd_rupture']/100)}\;kN\!\cdot\!m"
        )
        out += _step(
            "5.6", "Furos na mesa tracionada",
            "Compara-se a força resistente da área líquida à exigência baseada na área bruta. Se a condição não for atendida, limita-se o momento pela ruptura.",
            _eq(
                r"Y_t=\begin{cases}1{,}00,&\dfrac{f_y}{f_u}\le0{,}80\\1{,}10,&\dfrac{f_y}{f_u}>0{,}80\end{cases}",
                r"A_{fg}=b_f\cdot t_f", r"A_{fn}=A_{fn,informada}",
                r"\rho_A=\frac{A_{fn}}{A_{fg}}",
                r"N_{u,liq}=f_u\cdot A_{fn}", r"N_{y,br}=Y_t\cdot f_y\cdot A_{fg}",
                r"M_{Rd,rupt}=\frac{f_u\cdot A_{fn}}{A_{fg}}\cdot\frac{W_x}{\gamma_{a2}}",
            ),
            _eq(
                rf"Y_t=\begin{{cases}}1.00,&\dfrac{{{_n(fy)}}}{{{_n(fu)}}}\le0.80\\1.10,&\dfrac{{{_n(fy)}}}{{{_n(fu)}}}>0.80\end{{cases}}={_n(f['Yt'],2)}",
                rf"A_{{fg}}={_n(p['bf'])}\cdot{_n(p['tf'])}={_n(Afg)}\;cm^2", rf"A_{{fn}}={_n(Afn)}\;cm^2",
                rf"\frac{{A_{{fn}}}}{{A_{{fg}}}}=\frac{{{_n(Afn)}}}{{{_n(Afg)}}}={_n(Afn_over_Afg,4)}",
                rf"f_u\cdot A_{{fn}}={_n(fu)}\cdot{_n(Afn)}={_n(fu*Afn)}\;kN",
                rf"Y_t\cdot f_y\cdot A_{{fg}}={_n(f['Yt'])}\cdot{_n(fy)}\cdot{_n(Afg)}={_n(f['Yt']*fy*Afg)}\;kN",
                (rf"M_{{Rd,rupt}}=\frac{{{_n(fu)}\cdot{_n(Afn)}\cdot{_n(p['Wx'])}}}{{{_n(Afg)}\cdot100\cdot{_n(gamma2,2)}}}={rupture_display}" if f["Mrd_rupture"] is not None else rf"M_{{Rd,rupt}}={rupture_display}\quad\left({_n(fu*Afn)}\ge{_n(f['Yt']*fy*Afg)}\right)"),
            ),
            f"Condição da área líquida: <strong>{'atendida — a ruptura não limita' if f['rupture_condition_ok'] else 'não atendida — aplicar o limite por ruptura'}</strong>.",
            "ABNT NBR 8800:2024, 5.4.2.6.",
        )
    candidate_symbols = []
    candidate_values = []
    if f["Mrd_FLT"] is not None:
        candidate_symbols.append(r"M_{Rd,FLT}")
        candidate_values.append(rf"M_{{Rd,FLT}}={_n(f['Mrd_FLT']/100)}\;kN\!\cdot\!m")
    candidate_symbols.extend([
        r"M_{Rd,FLM}",
        r"M_{Rd,alma\;ou\;mesa\;t}",
        r"M_{Rd,lim}",
    ])
    candidate_values.extend([
        rf"M_{{Rd,FLM}}={_n(f['Mrd_FLM']/100)}\;kN\!\cdot\!m",
        rf"M_{{Rd,alma\;ou\;mesa\;t}}={_n(f['Mrd_FLA_or_tension']/100)}\;kN\!\cdot\!m",
        rf"M_{{Rd,lim}}={_n(f['cap_5_4_2_2']/100)}\;kN\!\cdot\!m",
    ])
    if f.get("Mrd_rupture") is not None:
        candidate_symbols.append(r"M_{Rd,rupt}")
        candidate_values.append(rf"M_{{Rd,rupt}}={_n(f['Mrd_rupture']/100)}\;kN\!\cdot\!m")
    governing_symbolic = (
        r"M_{Rd}=\min\left\{\begin{gathered}"
        + r"\\[5pt]".join(candidate_symbols)
        + r"\end{gathered}\right\}"
    )
    governing_numeric = (
        r"M_{Rd}=\min\left\{\begin{gathered}"
        + r"\\[5pt]".join(candidate_values)
        + r"\end{gathered}\right\}="
        + _n(f["Mrd"] / 100)
        + r"\;kN\!\cdot\!m"
    )
    out += _step(
        "5.7", "Resistência governante à flexão",
        "A resistência de cálculo é o menor valor entre todos os estados-limites aplicáveis e o limite geral. Pendências de aplicabilidade forçam resistência global nula no núcleo.",
        governing_symbolic,
        governing_numeric,
        f"Resistência governante: <strong>{_n(f['Mrd']/100)} kN·m</strong>.", f["reference"],
    )
    eff = Msd / f["Mrd"] * 100 if f["Mrd"] > 0 else math.inf
    status = "APROVADO" if Msd <= f["Mrd"] and f["Mrd"] > 0 else "REPROVADO" if f["Mrd"] > 0 else "NÃO VERIFICADO"
    out += _verification("Flexão — estado-limite governante", Msd/100, f["Mrd"]/100, r"kN\!\cdot\!m", status, eff, "M_{Sd}", "M_{Rd}", f["reference"])
    return out


def _annex_e_step(bundle):
    f, p = bundle["flexure"], bundle["props"]
    fy, E, gamma1 = bundle["fy"], bundle["E"], bundle["gamma_a1"]
    if f["regime_FLT"] == "plástico":
        active = r"M_{Rd,FLT}=\min\left(\frac{M_y}{\gamma_{a1}};M_{Rd,lim}\right)"
        active_numeric = rf"M_{{Rd,FLT}}=\min\left(\frac{{{_n(f['M_y_annex_e']/100)}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n((f['Mrd_FLT'] or 0)/100)}\;kN\!\cdot\!m"
    elif f["regime_FLT"] == "inelástico":
        active = r"M_{Rd,FLT}=\min\left(\frac{M_y-(M_y-M_r)\cdot\dfrac{\lambda_{LT}-\lambda_p}{\lambda_r-\lambda_p}}{\gamma_{a1}};M_{Rd,lim}\right)"
        active_numeric = rf"M_{{Rd,FLT}}=\min\left(\frac{{{_n(f['M_y_annex_e']/100)}-({_n(f['M_y_annex_e']/100)}-{_n(f['M_r_annex_e']/100)})\cdot\dfrac{{{_n(f['lambda_LT'])}-{_n(f['lambda_p_LT_annex_e'])}}}{{{_n(f['lambda_r_LT_annex_e'])}-{_n(f['lambda_p_LT_annex_e'])}}}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n((f['Mrd_FLT'] or 0)/100)}\;kN\!\cdot\!m"
    else:
        active = r"M_{Rd,FLT}=\min\left(\frac{M_{cr}}{\gamma_{a1}};M_{Rd,lim}\right)"
        active_numeric = rf"M_{{Rd,FLT}}=\min\left(\frac{{{_n(f['Mcr_FLT']/100)}}}{{{_n(gamma1,2)}}};{_n(f['cap_5_4_2_2']/100)}\right)={_n((f['Mrd_FLT'] or 0)/100)}\;kN\!\cdot\!m"
    return _step(
        "5.3", "Anexo E — alma esbelta e FLT",
        "Para perfil soldado com alma esbelta verificam-se o limite geométrico, ar e o fator de redução kpg. A FLT é calculada com as propriedades da mesa comprimida associada a 1/6 da alma.",
        _eq(
            r"a_r=\frac{h_c\cdot t_w}{A_c}",
            r"k_{pg}=1-\frac{a_r}{1200+300\cdot a_r}\cdot\left(\frac{h_c}{t_w}-5{,}70\cdot\sqrt{\frac{E}{f_y}}\right)",
            r"I_{yc}=\frac{t_f\cdot b_f^3}{12}+\frac{\left(\dfrac{h_c}{6}\right)\cdot t_w^3}{12}",
            r"A_{yc}=b_f\cdot t_f+\frac{h_c}{6}\cdot t_w",
            r"r_{yc}=\sqrt{\frac{I_{yc}}{A_{yc}}}",
            r"\lambda_{LT}=\frac{L_b}{r_{yc}}",
            r"\lambda_p=1{,}10\cdot\sqrt{\frac{E}{f_y}}",
            r"\lambda_r=\pi\cdot\sqrt{\frac{E}{f_y-\sigma_r}}",
            r"M_y=k_{pg}\cdot f_y\cdot W_{xc}",
            r"M_r=k_{pg}\cdot(f_y-\sigma_r)\cdot W_{xc}",
            r"M_{cr}=\frac{C_b\cdot k_{pg}\cdot\pi^2\cdot E\cdot W_{xc}}{\lambda_{LT}^2}", active,
        ),
        _eq(
            rf"a_r=\frac{{{_n(f['hc'])}\cdot{_n(p['tw'])}}}{{{_n(p['bf'])}\cdot{_n(p['tf'])}}}={_n(f['ar'])}",
            rf"k_{{pg}}=1-\frac{{{_n(f['ar'])}}}{{1200+300\cdot{_n(f['ar'])}}}\cdot\left(\frac{{{_n(f['hc'])}}}{{{_n(p['tw'])}}}-5.70\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}\right)={_n(f['kpg'],4)}",
            rf"I_{{yc}}=\frac{{{_n(p['tf'])}\cdot{_n(p['bf'])}^3}}{{12}}+\frac{{\left(\dfrac{{{_n(f['hc'])}}}{{6}}\right)\cdot{_n(p['tw'])}^3}}{{12}}={_n(f['Iyc'])}\;cm^4",
            rf"A_{{yc}}={_n(p['bf'])}\cdot{_n(p['tf'])}+\frac{{{_n(f['hc'])}}}{{6}}\cdot{_n(p['tw'])}={_n(f['Ayc'])}\;cm^2",
            rf"r_{{yc}}=\sqrt{{\frac{{{_n(f['Iyc'])}}}{{{_n(f['Ayc'])}}}}}={_n(f['ryc'])}\;cm",
            rf"\lambda_{{LT}}=\frac{{{_n(bundle['Lb'])}}}{{{_n(f['ryc'])}}}={_n(f['lambda_LT'])}",
            rf"\lambda_p=1.10\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}={_n(f['lambda_p_LT_annex_e'])}",
            rf"\lambda_r=\pi\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}-{_n(f['sigma_r'])}}}}}={_n(f['lambda_r_LT_annex_e'])}",
            rf"M_y=\frac{{{_n(f['kpg'],4)}\cdot{_n(fy)}\cdot{_n(f['Wxc'])}}}{{100}}={_n(f['M_y_annex_e']/100)}\;kN\!\cdot\!m",
            rf"M_r=\frac{{{_n(f['kpg'],4)}\cdot({_n(fy)}-{_n(f['sigma_r'])})\cdot{_n(f['Wxc'])}}}{{100}}={_n(f['M_r_annex_e']/100)}\;kN\!\cdot\!m",
            rf"M_{{cr}}=\frac{{{_n(bundle['Cb'],4)}\cdot{_n(f['kpg'],4)}\cdot\pi^2\cdot{_n(E)}\cdot{_n(f['Wxc'])}}}{{{_n(f['lambda_LT'])}^2\cdot100}}={_n(f['Mcr_FLT']/100)}\;kN\!\cdot\!m",
            active_numeric,
        ),
        f"kpg = <strong>{_n(f['kpg'],4)}</strong>; MRd,FLT = <strong>{_n((f['Mrd_FLT'] or 0)/100)} kN·m</strong>; limite da razão entre h e tw no Anexo E = {_n(f['annex_e_limit'])}.",
        "ABNT NBR 8800:2024, Anexo E.", f["regime_FLT"],
    )


def _shear_section(bundle):
    s, p = bundle["shear"], bundle["props"]
    fy, E, gamma1, Vsd = bundle["fy"], bundle["E"], bundle["gamma_a1"], bundle["Vsd"]
    out = _chapter("6. Resistência ao cisalhamento", "A alma é classificada, os enrijecedores são validados quando declarados e o ramo resistente é mostrado explicitamente.") + _shear_theory()
    if s["stiffener_valid"]:
        kv_symbolic = r"k_v=5+\frac{5}{\left(\dfrac{a}{h}\right)^2}"
        kv_numeric = rf"k_v=5+\frac{{5}}{{\left(\dfrac{{{_n(s['a_h']*p['h_clear'])}}}{{{_n(p['h_clear'])}}}\right)^2}}={_n(s['kv'])}"
    else:
        kv_symbolic = r"k_v=5{,}34\quad\text{(sem enrijecedor eficaz)}"
        kv_numeric = rf"k_v=5.34={_n(s['kv'])}"
    out += _step(
        "6.1", "Esbeltez da alma e coeficiente kv",
        "O coeficiente kv só considera enrijecedores transversais quando soldagem, esbeltez e inércia são atendidas; caso contrário, o núcleo usa kv = 5,34.",
        _eq(
            r"\lambda=\frac{h}{t_w}",
            kv_symbolic,
        ),
        _eq(
            rf"\lambda=\frac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}={_n(s['lambda'])}",
            kv_numeric,
        ),
        f"kv = <strong>{_n(s['kv'])}</strong> — {_esc(s['kv_basis'])}.", s["reference"],
    )
    if s["stiffener_requested"]:
        checks = {c["name"]: c for c in s["stiffener_checks"]}
        out += _step(
            "6.2", "Validação dos enrijecedores transversais",
            "A Errata 1:2025 corrige a expressão de j. A inércia é calculada em relação ao eixo no plano médio da alma e comparada ao mínimo requerido.",
            _eq(
                r"j=\max\left[\frac{2{,}5}{\left(\dfrac{a}{h}\right)^2}-2;\;0{,}5\right]",
                r"I_{st}\ge I_{req}=a\cdot t_w^3\cdot j",
                r"\frac{b}{t}\le0{,}56\cdot\sqrt{\frac{E}{f_y}}",
            ),
            _eq(
                rf"j=\max\left[\frac{{2.5}}{{\left(\dfrac{{{_n(s['a_h']*p['h_clear'])}}}{{{_n(p['h_clear'])}}}\right)^2}}-2;\;0.5\right]={_n(s['j'])}",
                rf"I_{{st}}={_n(s['I_st'])}\; {'\\ge' if checks['inércia']['passed'] else '<'}\; I_{{req}}={_n(s['a_h']*p['h_clear'])}\cdot{_n(p['tw'])}^3\cdot{_n(s['j'])}={_n(s['I_required'])}\;cm^4",
                rf"\frac{{b}}{{t}}=\frac{{{_n(s['stiffener_width'])}}}{{{_n(s['stiffener_thickness'])}}}={_n(s['stiffener_slenderness'])}\; {'\\le' if checks['b/t']['passed'] else '>'}\;0.56\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}={_n(s['stiffener_slenderness_limit'])}",
            ),
            f"Enrijecedor <strong>{'validado' if s['stiffener_valid'] else 'não validado'}</strong>; soldagem às mesas e à alma: {'sim' if checks['soldagem']['passed'] else 'não'}.",
            s["reference"], "Somente enrijecedores integralmente aprovados alteram kv.",
        )
    step_no = "6.3" if s["stiffener_requested"] else "6.2"
    if s["regime"] == "escoamento":
        active = r"V_{Rd}=\frac{V_{pl}}{\gamma_{a1}}"
    elif "inelástica" in s["regime"]:
        active = r"V_{Rd}=\frac{\lambda_p}{\lambda}\cdot\frac{V_{pl}}{\gamma_{a1}}"
    else:
        active = r"V_{Rd}=1{,}24\cdot\left(\frac{\lambda_p}{\lambda}\right)^2\cdot\frac{V_{pl}}{\gamma_{a1}}"
    if s["regime"] == "escoamento":
        active_numeric = rf"V_{{Rd}}=\frac{{{_n(s['Vpl'])}}}{{{_n(gamma1,2)}}}={_n(s['Vrd'])}\;kN"
    elif "inelástica" in s["regime"]:
        active_numeric = rf"V_{{Rd}}=\frac{{{_n(s['lambda_p'])}}}{{{_n(s['lambda'])}}}\cdot\frac{{{_n(s['Vpl'])}}}{{{_n(gamma1,2)}}}={_n(s['Vrd'])}\;kN"
    else:
        active_numeric = rf"V_{{Rd}}=1.24\cdot\left(\frac{{{_n(s['lambda_p'])}}}{{{_n(s['lambda'])}}}\right)^2\cdot\frac{{{_n(s['Vpl'])}}}{{{_n(gamma1,2)}}}={_n(s['Vrd'])}\;kN"
    out += _step(
        step_no, "Resistência da alma ao cisalhamento",
        "Os limites λp e λr identificam escoamento, flambagem inelástica ou flambagem elástica. A fórmula ativa é registrada abaixo.",
        _eq(
            r"\lambda=\frac{h}{t_w}",
            r"V_{pl}=0{,}60\cdot d\cdot t_w\cdot f_y",
            r"\lambda_p=1{,}10\cdot\sqrt{\frac{k_v\cdot E}{f_y}}",
            r"\lambda_r=1{,}37\cdot\sqrt{\frac{k_v\cdot E}{f_y}}", active,
        ),
        _eq(
            rf"\lambda=\frac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}={_n(s['lambda'])}",
            rf"V_{{pl}}=0.60\cdot{_n(p['d'])}\cdot{_n(p['tw'])}\cdot{_n(fy)}={_n(s['Vpl'])}\;kN",
            rf"\lambda_p=1.10\cdot\sqrt{{\frac{{{_n(s['kv'])}\cdot{_n(E)}}}{{{_n(fy)}}}}}={_n(s['lambda_p'])}",
            rf"\lambda_r=1.37\cdot\sqrt{{\frac{{{_n(s['kv'])}\cdot{_n(E)}}}{{{_n(fy)}}}}}={_n(s['lambda_r'])}",
            active_numeric,
        ),
        f"VRd = <strong>{_n(s['Vrd'])} kN</strong>; regime {s['regime']}.", s["reference"], s["regime"],
    )
    status = "APROVADO" if Vsd <= s["Vrd"] else "REPROVADO"
    out += _verification("Cisalhamento", Vsd, s["Vrd"], "kN", status, Vsd/s["Vrd"]*100, "V_{Sd}", "V_{Rd}", s["reference"])
    return out


def _local_section(bundle):
    checks, p = bundle.get("local_checks", []), bundle["props"]
    fy, E, gamma1 = bundle["fy"], bundle["E"], bundle["gamma_a1"]
    out = _chapter("7. Forças transversais localizadas", "Cada reação e força pontual é verificada contra escoamento local, enrugamento e, quando aplicável, flambagem lateral da alma.") + _local_theory()
    if not checks:
        return out + '<div class="notice pending"><strong>Não calculado.</strong> O modo manual não fornece reações, comprimentos de atuação e posições suficientes. A verificação externa deve ser documentada.</div>'
    for index, check in enumerate(checks, 1):
        d = check["details"]
        out += f'<h3>7.{index} {_esc(check["name"])} — x = {_n(check.get("position",0)/100)} m</h3>'
        yield_symbolic = r"F_{Rd,y}=\frac{1{,}10\cdot(5\cdot k+\ell_n)\cdot f_y\cdot t_w}{\gamma_{a1}}" if d["distance_to_end"] > p["d"] else r"F_{Rd,y}=\frac{1{,}10\cdot(2{,}5\cdot k+\ell_n)\cdot f_y\cdot t_w}{\gamma_{a1}}"
        factor = 5.0 if d["distance_to_end"] > p["d"] else 2.5
        out += _step(
            f"7.{index}.1", "Escoamento local da alma",
            "Para perfil laminado, k inclui o raio entre mesa e alma; para perfil soldado, inclui a dimensão da solda informada. A posição define o caso interno ou próximo à extremidade.",
            _eq(r"k=t_f+k_{raiz}", r"\ell_n=\ell_{n,informado}", yield_symbolic),
            _eq(
                rf"k={_n(d['k'])}\;cm", rf"\ell_n={_n(d['bearing_length'])}\;cm",
                rf"F_{{Rd,y}}=\frac{{1.10\cdot[{_n(factor,1)}\cdot{_n(d['k'])}+{_n(d['bearing_length'])}]\cdot{_n(fy)}\cdot{_n(p['tw'])}}}{{{_n(gamma1,2)}}}={_n(d['yielding_FRd'])}\;kN",
            ),
            f"FRd,y = <strong>{_n(d['yielding_FRd'])} kN</strong>; {d['yielding_case']}.", d["reference"], d["yielding_case"],
        )
        if d["crippling_case"] == "seção interna":
            coeff, bracket = .66, r"1+3\cdot\frac{\ell_n}{d}\cdot\left(\frac{t_w}{t_f}\right)^{1{,}5}"
            bracket_numeric = rf"1+3\cdot\frac{{{_n(d['bearing_length'])}}}{{{_n(p['d'])}}}\cdot\left(\frac{{{_n(p['tw'])}}}{{{_n(p['tf'])}}}\right)^{{1.5}}"
        elif "≤" in d["crippling_case"]:
            coeff, bracket = .33, r"1+3\cdot\frac{\ell_n}{d}\cdot\left(\frac{t_w}{t_f}\right)^{1{,}5}"
            bracket_numeric = rf"1+3\cdot\frac{{{_n(d['bearing_length'])}}}{{{_n(p['d'])}}}\cdot\left(\frac{{{_n(p['tw'])}}}{{{_n(p['tf'])}}}\right)^{{1.5}}"
        else:
            coeff, bracket = .33, r"1+\left(4\cdot\frac{\ell_n}{d}-0{,}2\right)\cdot\left(\frac{t_w}{t_f}\right)^{1{,}5}"
            bracket_numeric = rf"1+\left(4\cdot\frac{{{_n(d['bearing_length'])}}}{{{_n(p['d'])}}}-0.2\right)\cdot\left(\frac{{{_n(p['tw'])}}}{{{_n(p['tf'])}}}\right)^{{1.5}}"
        out += _step(
            f"7.{index}.2", "Enrugamento da alma",
            "A rotina seleciona o coeficiente e o termo de amplificação conforme a distância à extremidade e a razão entre ℓn e d.",
            rf"F_{{Rd,cr}}=\frac{{{_n(coeff,2)}\cdot t_w^2}}{{\gamma_{{a1}}}}\cdot\left[{bracket}\right]\cdot\sqrt{{\frac{{E\cdot f_y\cdot t_f}}{{t_w}}}}",
            rf"F_{{Rd,cr}}=\frac{{{_n(coeff,2)}\cdot{_n(p['tw'])}^2}}{{{_n(gamma1,2)}}}\cdot\left[{bracket_numeric}\right]\cdot\sqrt{{\frac{{{_n(E)}\cdot{_n(fy)}\cdot{_n(p['tf'])}}}{{{_n(p['tw'])}}}}}={_n(d['crippling_FRd'])}\;kN",
            f"FRd,cr = <strong>{_n(d['crippling_FRd'])} kN</strong>; {d['crippling_case']}.", d["reference"], d["crippling_case"],
        )
        if d.get("sidesway_FRd") is not None:
            sidesway_res = f"{_n(d['sidesway_FRd'])} kN"
            ell_local = p["bf"] * (p["h_clear"] / p["tw"]) / d["sidesway_ratio"]
            if d["kpg_local"] < 1.0:
                kpg_symbolic = r"k_{pg}=1-\frac{a_r}{1200+300\cdot a_r}\cdot\left(\frac{h}{t_w}-5{,}70\cdot\sqrt{\frac{E}{f_y}}\right)"
                ar_local = p["h_clear"] * p["tw"] / (p["bf"] * p["tf"])
                kpg_numeric = rf"k_{{pg}}=1-\frac{{{_n(ar_local)}}}{{1200+300\cdot{_n(ar_local)}}}\cdot\left(\frac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}-5.70\cdot\sqrt{{\frac{{{_n(E)}}}{{{_n(fy)}}}}}\right)={_n(d['kpg_local'],4)}"
            else:
                kpg_symbolic = r"k_{pg}=1{,}00\quad\text{(alma não esbelta para esta verificação)}"
                kpg_numeric = rf"k_{{pg}}=1.00={_n(d['kpg_local'],4)}"
            cr_factor = d["Cr"] / E
            rotation_term = r"0{,}94+0{,}37\cdot\eta^3" if "impedida" in d["sidesway_case"] and "não" not in d["sidesway_case"] else r"0{,}37\cdot\eta^3"
            rotation_term_numeric = rf"0.94+0.37\cdot{_n(d['sidesway_ratio'])}^3" if "impedida" in d["sidesway_case"] and "não" not in d["sidesway_case"] else rf"0.37\cdot{_n(d['sidesway_ratio'])}^3"
            out += _step(
                f"7.{index}.3", "Flambagem lateral da alma",
                "Verifica-se primeiro o critério geométrico. Quando o fenômeno pode ocorrer, Cr é 32E ou 16E conforme o momento local e a resistência de início de escoamento; a contenção de rotação da mesa define a expressão final.",
                _eq(
                    r"\eta=\frac{\dfrac{h}{t_w}}{\dfrac{\ell}{b_f}}",
                    kpg_symbolic,
                    r"M_r=k_{pg}\cdot f_y\cdot W_x",
                    r"C_r=\begin{cases}32\cdot E,&|M_{Sd,local}|<M_r\\16\cdot E,&|M_{Sd,local}|\ge M_r\end{cases}",
                    rf"F_{{Rd,lat}}=\frac{{C_r\cdot t_w^3\cdot t_f}}{{\gamma_{{a1}}\cdot h^2}}\cdot\left({rotation_term}\right)",
                ),
                _eq(
                    rf"\eta=\frac{{\dfrac{{{_n(p['h_clear'])}}}{{{_n(p['tw'])}}}}}{{\dfrac{{{_n(ell_local)}}}{{{_n(p['bf'])}}}}}={_n(d['sidesway_ratio'])}",
                    kpg_numeric,
                    rf"M_r=\frac{{{_n(d['kpg_local'],4)}\cdot{_n(fy)}\cdot{_n(p['Wx'])}}}{{100}}={_n((d['Mr'] or 0)/100)}\;kN\!\cdot\!m",
                    rf"C_r={_n(cr_factor,0)}\cdot{_n(E)}={_n(d['Cr'])}\;kN/cm^2",
                    rf"F_{{Rd,lat}}=\frac{{{_n(d['Cr'])}\cdot{_n(p['tw'])}^3\cdot{_n(p['tf'])}}}{{{_n(gamma1,2)}\cdot{_n(p['h_clear'])}^2}}\cdot\left({rotation_term_numeric}\right)={_n(d['sidesway_FRd'])}\;kN",
                ),
                f"Resultado: <strong>{sidesway_res}</strong>; {d['sidesway_case']}.", d["reference"], d["sidesway_case"],
            )
        elif d.get("sidesway_ratio") is not None:
            out += _step(
                f"7.{index}.3", "Flambagem lateral da alma — critério geométrico",
                "O índice geométrico excede o limite aplicável; portanto, a flambagem lateral da alma não ocorre por este critério e nenhuma resistência fictícia é calculada.",
                r"\eta=\frac{\dfrac{h}{t_w}}{\dfrac{\ell}{b_f}}>\eta_{lim}",
                rf"\eta={_n(d['sidesway_ratio'])}>{_n(d['sidesway_limit'])}",
                f"Conclusão: <strong>{_esc(d['sidesway_case'])}</strong>.", d["reference"], d["sidesway_case"],
            )
        else:
            out += _step(
                f"7.{index}.3", "Flambagem lateral da alma — aplicabilidade",
                "Este estado-limite exige deslocamento lateral relativo entre a mesa comprimida carregada e a mesa tracionada. A condição de contenção declarada é verificada antes de qualquer resistência numérica.",
                r"\text{movimento lateral relativo impedido}",
                r"F_{Rd,lat}=\mathrm{N/A}",
                f"Conclusão: <strong>{_esc(d['sidesway_case'])}</strong>.", d["reference"], d["sidesway_case"],
            )
        values = [f"escoamento {_n(d['yielding_FRd'])}", f"enrugamento {_n(d['crippling_FRd'])}"]
        if d.get("sidesway_FRd") is not None:
            values.append(f"flambagem lateral {_n(d['sidesway_FRd'])}")
        out += _step(
            f"7.{index}.4", "Resistência local governante",
            "A menor resistência entre os estados-limites aplicáveis governa a força transversal localizada.",
            r"F_{Rd}=\min(F_{Rd,y},F_{Rd,cr},F_{Rd,lat})",
            r"F_{Rd}=\min(" + r";\;".join(values) + rf")={_n(check['resistance'])}\;kN",
            f"FRd = <strong>{_n(check['resistance'])} kN</strong>.", d["reference"],
        )
        out += _verification(check["name"], check["demand"], check["resistance"], "kN", check["status"], check["efficiency"], "F_{Sd}", "F_{Rd}", d["reference"])
    out += '<div class="notice">O detalhamento executivo de enrijecedores locais e respectivas soldas permanece sujeito ao item 5.7.9.</div>'
    return out


def _els_section(bundle):
    response, loads = bundle.get("els_response"), bundle.get("els_loads")
    out = _chapter("8. Estado-limite de serviço — deslocamento", "A combinação de serviço e a integração da linha elástica são apresentadas separadamente do ELU.") + _els_theory()
    if not response or not loads:
        return out + '<div class="notice pending"><strong>Não calculado.</strong> O modo manual não contém ações de serviço suficientes para reconstruir a flecha.</div>'
    factor = loads["variable_factor"]
    permanent = r"q_{G,k}+q_{pp,k}+" if loads["include_permanent"] else ""
    permanent_p = r"P_{G,k}+" if loads["include_permanent"] else ""
    out += _step(
        "8.1", "Combinação de serviço",
        "O fator ψ é selecionado conforme a combinação rara, frequente, quase permanente ou somente variável declarada. Nenhum coeficiente de ELU é reutilizado no ELS.",
        _eq(rf"q_s={permanent}\psi\cdot q_{{Q,k}}", rf"P_s={permanent_p}\psi\cdot P_{{Q,k}}"),
        _eq(
            rf"q_s={_n((loads['q_permanent'] if loads['include_permanent'] else 0)*100)}+{_n((loads['self_weight'] if loads['include_permanent'] else 0)*100)}+{_n(factor,2)}\cdot{_n(loads['q_variable']*100)}={_n(loads['q']*100)}\;kN/m",
            rf"P_s={_n(loads['point_permanent'] if loads['include_permanent'] else 0)}+{_n(factor,2)}\cdot{_n(loads['point_variable'])}={_n(loads['P'])}\;kN",
        ),
        f"Combinação: <strong>{_esc(bundle['els_combination_text'])}</strong>; qs = {_n(loads['q']*100)} kN/m; Ps = {_n(loads['P'])} kN.", loads["reference"],
    )
    x_d = response.max_deflection_position
    p_d_term = max(x_d - response.point_position, 0.0)
    d_index = min(range(len(response.x)), key=lambda idx: abs(response.x[idx] - x_d))
    v_signed = response.deflections[d_index]
    out += _step(
        "8.2", "Linha elástica por funções de singularidade",
        "A equação EI·v(x) é a dupla integração do momento fletor. A constante C1 satisfaz as condições de contorno; a máxima flecha é pesquisada na malha da viga incluindo a posição da força pontual.",
        _eq(
            r"E\cdot I_x\cdot v(x)=C_1\cdot x+\frac{M_A\cdot x^2}{2}+\frac{R_A\cdot x^3}{6}-\frac{q_s\cdot x^4}{24}-\frac{P_s\cdot\langle x-a\rangle^3}{6}",
            r"\delta_{max}=\max_x\left|v(x)\right|",
        ),
        _eq(
            rf"v({_n(x_d)})=\frac{{{_n(response.rotation_integration_constant)}\cdot{_n(x_d)}+\dfrac{{{_n(response.moment_left)}\cdot{_n(x_d)}^2}}{{2}}+\dfrac{{{_n(response.reaction_left)}\cdot{_n(x_d)}^3}}{{6}}-\dfrac{{{_n(response.q,6)}\cdot{_n(x_d)}^4}}{{24}}-\dfrac{{{_n(response.point_load)}\cdot{_n(p_d_term)}^3}}{{6}}}}{{{_n(bundle['E'])}\cdot{_n(bundle['props']['Ix'])}}}={_n(v_signed,4)}\;cm",
            rf"\delta_{{max}}=\max_x\left|v(x)\right|=\left|{_n(v_signed,4)}\right|={_n(response.max_deflection,4)}\;cm\quad(x={_n(x_d/100)}\;m)",
        ),
        f"Flecha máxima = <strong>{_n(response.max_deflection,4)} cm</strong> em x = {_n(response.max_deflection_position/100)} m.",
        "ABNT NBR 8800:2024, 4.8.7.3 e Anexo B; análise elástica do aplicativo.",
    )
    reference_length = 2 * bundle["length"] if response.support == "cantilever" else bundle["length"]
    relative_limit = reference_length / bundle["deflection_divisor"]
    limit_numeric_lines = [
        rf"\delta_{{lim,rel}}=\frac{{{_n(reference_length)}}}{{{_n(bundle['deflection_divisor'],0)}}}={_n(relative_limit,4)}\;cm"
    ]
    if bundle.get("masonry_on_beam"):
        limit_numeric_lines.extend([
            r"\delta_{lim,abs}=1{,}50\;cm",
            rf"\delta_{{lim}}=\min\left({_n(relative_limit,4)};\;1.50\right)={_n(bundle['deflection_limit'],4)}\;cm",
        ])
    limit_symbolic_lines = [r"\delta_{lim,rel}=\frac{L_{ref}}{n}"]
    if bundle.get("masonry_on_beam"):
        limit_symbolic_lines.extend([
            r"\delta_{lim,abs}=1{,}50\;cm",
            r"\delta_{lim}=\min(\delta_{lim,rel};\delta_{lim,abs})",
        ])
    out += _step(
        "8.3", "Deslocamento limite",
        "Para balanço, a norma usa como comprimento de referência o dobro do comprimento teórico. Quando há alvenaria, aplica-se também o limite absoluto declarado de 15 mm.",
        _eq(*limit_symbolic_lines),
        _eq(*limit_numeric_lines),
        f"Limite adotado = <strong>{_n(bundle['deflection_limit'],4)} cm</strong>.",
        "ABNT NBR 8800:2024, Anexo B.",
    )
    out += _verification("Deslocamento vertical", response.max_deflection, bundle["deflection_limit"], "cm", bundle["deflection_status"], bundle["deflection_efficiency"], r"\delta_{max}", r"\delta_{lim}", "ABNT NBR 8800:2024, Anexo B")
    return out


def _scope_section(bundle):
    notes = "".join(f"<li>{_esc(item)}</li>" for item in bundle.get("scope_notes", [])) or "<li>Nenhuma hipótese adicional registrada.</li>"
    issues = "".join(f"<li>{_esc(item)}</li>" for item in bundle.get("scope_issues", [])) or "<li>Nenhuma pendência declarada.</li>"
    cls = _status_class(bundle["status_global"])
    return f"""
    {_chapter('9. Escopo, hipóteses e conclusão', 'O status global inclui resistências, serviço, forças localizadas e limitações de aplicabilidade.')}
    <div class="scope-grid">
      <div class="info-card"><h4>Hipóteses adotadas</h4><ul>{notes}</ul></div>
      <div class="info-card"><h4>Pendências e exclusões</h4><ul>{issues}</ul></div>
    </div>
    <div class="global-status {cls}"><span>STATUS GLOBAL</span><strong>{_esc(bundle['status_global'])}</strong></div>
    <div class="notice"><strong>Nota de responsabilidade:</strong> este memorial documenta o modelo declarado e não substitui a revisão do engenheiro responsável, o detalhamento das ligações, a estabilidade global da estrutura nem verificações fora do escopo explicitado.</div>
    """


def build_memorial_details(bundle):
    """Monta o memorial visual completo sem alterar resultados de cálculo."""
    return (
        '<div class="audit-banner"><strong>MEMORIAL AUDITÁVEL</strong><span>Equações, verificações e decisões normativas</span></div>'
        + _beam_actions(bundle)
        + _cb_section(bundle)
        + _flexure_section(bundle)
        + _shear_section(bundle)
        + _local_section(bundle)
        + _els_section(bundle)
        + _scope_section(bundle)
    )
