from aiogram.fsm.state import State, StatesGroup

class SessionState(StatesGroup):
    waiting_for_session = State()

class TargetState(StatesGroup):
    waiting_for_username = State()

class ReportState(StatesGroup):
    selecting_types = State()
    waiting_for_random_count = State()   # جديد

class BroadcastState(StatesGroup):
    waiting_for_message = State()
