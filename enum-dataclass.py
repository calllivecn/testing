import enum
import pickle
from dataclasses import dataclass

from typing import Self

# 两边传输
class CmdType(enum.IntEnum):
    
    Status = 0x01
    Task = enum.auto()
    List = enum.auto()
    Insert = enum.auto()
    Remove = enum.auto()
    Move = enum.auto()
    Done = enum.auto()

    ADD = enum.auto()
    Kill = enum.auto()
    Pause = enum.auto()
    Recover = enum.auto()

    # 回复client的type
    ReOK = enum.auto()
    ReERR = enum.auto()
    Result = enum.auto()

@dataclass
class CmdProtocol:
    CmdType: CmdType
    task_number: int|None = None
    reply: str|None = None

    def dumps(self) -> bytes:
        return pickle.dumps(self)

    @classmethod
    def loads(cls, data: bytes) -> Self:
        """
        try:
            proto = pickle.loads(data)
        except Exception as e:
            logger.error(f"加载协议异常: {e}")
            traceback.print_exc()
            return None

        if isinstance(proto, cls):
            return proto
        else:
            logger.error("加载协议失败，类型不匹配")
            return None
        """
        return pickle.loads(data)


if __name__ == "__main__":
    reply = CmdProtocol(CmdType=CmdType.List).dumps()
    print(f"{type(reply)=}  {dir(reply)=}")
    cp = CmdProtocol.loads(reply)
    print(f"{type(cp)=}  {dir(cp)=}")

