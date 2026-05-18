"""
流程指导服务 — 对应设计文档 4.12 TutorialService 类
"""
from app.repositories.tutorial_repository import TutorialRepository
from app.schemas.qa_schema import TutorialGuideResponse


class TutorialService:
    """根据工序名称获取标准化教程及步骤"""

    def __init__(self, tutorial_repo: TutorialRepository):
        self._tutorialRepository = tutorial_repo

    def getTutorial(self, processName: str) -> dict:
        """根据工序名称获取教程概览和步骤 — 对应 TutorialService.getTutorial"""
        if not processName or not processName.strip():
            raise ValueError("工序名称不能为空")

        name = processName.strip()
        tutorial = self._tutorialRepository.findByProcessName(name)
        if not tutorial:
            candidates = self._tutorialRepository.searchByProcessName(name)
            if candidates:
                tutorial = candidates[0]
            else:
                raise ValueError(f"未找到工序「{processName}」的教程")

        steps = self._tutorialRepository.getSteps(tutorial.tutorial_id)
        return self._buildTutorialResult(tutorial, steps)

    def getTutorialSteps(self, tutorialId: str) -> dict:
        """根据教程编号获取教程详情及步骤 — 对应 TutorialService.getTutorialSteps"""
        tutorial = self._tutorialRepository.findById(tutorialId)
        if not tutorial:
            raise ValueError("教程不存在")

        steps = self._tutorialRepository.getSteps(tutorialId)
        return self._buildTutorialResult(tutorial, steps)

    def _sortSteps(self, steps: list) -> list:
        """按步骤号排序 — 数据库已按 step_no 排序，直接返回"""
        return steps

    def _buildTutorialResult(self, tutorial, steps: list) -> dict:
        sorted_steps = self._sortSteps(steps)
        return TutorialGuideResponse(
            tutorialId=tutorial.tutorial_id,
            processName=tutorial.process_name,
            totalSteps=tutorial.total_steps,
            estimatedTime=tutorial.estimated_time,
            steps=[
                {
                    "stepId": s.step_id,
                    "stepNo": s.step_no,
                    "stepTitle": s.step_title,
                    "stepContent": s.step_content,
                    "imageUrl": s.image_url,
                    "note": s.note,
                    "faq": s.faq,
                }
                for s in sorted_steps
            ],
        ).model_dump()
