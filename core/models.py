from dataclasses import dataclass, field

@dataclass
class SuspiciousClaim:
    text: str
    
@dataclass
class SlideResult:
    slide_no: int
    raw_text: str
    cleaned_text: str
    verdict: str          # SUPPORTED / REFUTED / NOT_SURE / ERROR
    rationale: str
    suspicious_claims: list[SuspiciousClaim] = field(default_factory=list)


def results_to_markdown(results: list[SlideResult]) -> str:
    """
    SlideResult 一覧を Slack の mrkdwn で読みやすく整形。
    """
    lines: list[str] = []
    verdict_emoji = {"SUPPORTED": "🟢", "REFUTED": "🔴", "NOT_SURE": "🟡", "ERROR": "⚠️"}

    for r in results:
        emoji = verdict_emoji.get(r.verdict, "❔")
        lines.append(f"*Slide {r.slide_no}* — {emoji} *{r.verdict}*")
        lines.append(f"> {r.rationale}")

        if r.suspicious_claims:
            lines.append("_疑わしい文_ :warning:")
            for c in r.suspicious_claims:
                lines.append(f"> • {c.text}")
        else:
            lines.append(":white_check_mark: 追加で疑わしい文はありません")

        lines.append("")  
    return "\n".join(lines)
