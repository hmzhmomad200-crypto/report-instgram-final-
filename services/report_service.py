import asyncio
from typing import List, Dict, Callable, Awaitable
from utils.instagram_reporter import InstagramReporter, REPORT_TYPES
from config import MAX_CONCURRENT_REPORTS

class ReportService:
    def __init__(self):
        self.reporter = InstagramReporter()
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REPORTS)
    
    async def report(self, target_user_id: str, session_id: str, report_type: Dict) -> bool:
        """إرسال بلاغ واحد مباشرة"""
        return await self.reporter.report(target_user_id, session_id, report_type)
    
    async def run_reports(self, session_id: str, target_id: str, report_keys: List[str], progress_callback: Callable[[int, int, str, bool], Awaitable[None]]):
        total = len(report_keys)
        success_count = 0
        failed_count = 0
        
        for idx, key in enumerate(report_keys, 1):
            report_type = REPORT_TYPES[key]
            async with self.semaphore:
                success = await self.reporter.report(target_id, session_id, report_type)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                await progress_callback(idx, total, report_type['name'], success)
                await asyncio.sleep(1)
        
        return success_count, failed_count
