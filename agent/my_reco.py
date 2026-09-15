"""崩坏学园2 自定义识别。

find_template_any_roi：同一个模板图在多个候选 ROI 里各找一遍，返回命中的那个。
崩崩的活动入口、按钮位置会随活动和界面变化，写死一个 roi 经常认不到，
列几个候选区域比反复调坐标省事。

它借用 pipeline 里的 _内部_模板识别 节点做实际匹配（参数用 pipeline_override 临时覆盖），
所以那个节点必须存在 —— 在 00_通用.json 里。

注意两个容易踩的坑（对着已装的 maa-framework-python 核实过）：
  * maa.define.RecognitionDetail 没有 .hit 字段，「有没有命中」看的是 .box is None；
  * CustomRecognition.AnalyzeResult 的 detail 参数是 str，不是 dict，传字典会直接报错。
"""

import json

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition

_SCRATCH_NODE = "_内部_模板识别"


def _box_to_list(box):
    """box 可能是 Rect / List / Tuple / ndarray，统一转成 [x, y, w, h]。"""
    if box is None:
        return None
    try:
        values = [int(v) for v in box]
    except (TypeError, ValueError):
        return None
    return values if len(values) == 4 else None


@AgentServer.custom_recognition("find_template_any_roi")
class FindTemplateAnyRoi(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        param = json.loads(argv.custom_recognition_param or "{}") or {}
        template = param.get("template")
        rois = param.get("candidate_rois") or []
        threshold = float(param.get("threshold", 0.8))

        if not template:
            return CustomRecognition.AnalyzeResult(
                box=None, detail="template 不能为空"
            )
        if not isinstance(rois, list) or not rois:
            return CustomRecognition.AnalyzeResult(
                box=None, detail="candidate_rois 不能为空"
            )

        for index, roi in enumerate(rois):
            detail = context.run_recognition(
                _SCRATCH_NODE,
                argv.image,
                pipeline_override={
                    _SCRATCH_NODE: {
                        "template": template,
                        "roi": roi,
                        "threshold": threshold,
                    }
                },
            )
            if detail is None or detail.box is None:
                continue

            box = _box_to_list(detail.box)
            if box is None:
                print(f"[find_template_any_roi] 命中的 box 没法转换: {detail.box!r}")
                continue

            print(f"[find_template_any_roi] 第 {index + 1} 个候选区域命中: {box}")
            return CustomRecognition.AnalyzeResult(
                box=box,
                detail=json.dumps(
                    {"roi_index": index, "roi": roi, "template": template},
                    ensure_ascii=False,
                ),
            )

        return CustomRecognition.AnalyzeResult(
            box=None,
            detail=json.dumps(
                {"error": "所有候选区域都没找到", "candidate_count": len(rois)},
                ensure_ascii=False,
            ),
        )
