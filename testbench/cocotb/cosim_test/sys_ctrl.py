class sys_ctrl:
    def __init__(self, cosim_wrapper, firmware:list):
        self.cosim_wrapper = cosim_wrapper
        self.firmware = firmware

    async def execute(self):
        for inst in self.firmware:
            await self.cosim_wrapper.execute(inst, mode="sw")
        await self.cosim_wrapper.wait_compare()