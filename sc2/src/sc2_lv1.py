import sc2
from sc2 import run_game, maps, Race, Difficulty
# Race: 종족 Difficultly: 난이도
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
    CYBERNETICSCORE, STALKER
import random

# 부모클래스의 sc2.BotAI 상속, distribute_workers 는 한 미네랄당 최대 3명의 일꾼 대입
# iteration = 박복, async 동기화시키기? -> 기능수행
# async 기능을 반복적으로 수행하기위해 사용하는거 같음 (해당 작업이 진행되고있나 판단후
# 진행이 안되어있으면 싱크를 맞춘다 라고 해석됨)
class SentdeBot(sc2.BotAI):
    async def on_step(self, iteration): # interation 으로 계속 반복
        await self.distribute_workers() # 일꾼들 미네랄로 분배
        await self.build_worker() # 일꾼 생성
        await self.build_pylons() # 수정탑 생성
        await self.build_assimilators() # 가스 건설
        await self.expand() # 멀티 확장
        await self.offensive_force_buildings() # 게이트웨이, 인공제어소 건설
        await self.build_offensive_force() # 게이트웨이 유닛 생성
        await self.attack() # 공격

# 일꾼 생성
    async def build_worker(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

# 수정탑 건설
    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON): # 인구수가 5보다 적게남고(OK), 수정탑 건설 진행중인 수정탑이 없으면
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON): # 수정탑 건설 가능하면
                    await self.build(PYLON, near=nexuses.first) # 넥서스 근처에 수정탑 생성

# 가스 건설
    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus) # 넥서스 기준으로 주어진값 안의 영역
            for vaspene in vaspenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                    await self.do(worker.build(ASSIMILATOR, vaspene))

#멀티 확장
    async def expand(self):
        if self.units(NEXUS).amount < 3 and self.can_afford(NEXUS): # 넥서스 개수가 3개 미만 과 넥서스 생성이 가능하면
            await self.expand_now()

# 게이트웨이, 인공제어소 생성
    async def offensive_force_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random

            # 인공제어소 한번만 생성
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE): # 게이트웨이가 건설 되어 있고, 인공제어소가 없는 상태이면은
                    if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                        await self.build(CYBERNETICSCORE, near=pylon)

            elif len(self.units(GATEWAY)) < 3: # 게이트웨이 3개까지 생성
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)

# 게이트웨이에서 추적자 생성
    async def build_offensive_force(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.can_afford(STALKER) and self.supply_left > 0:
                await self.do(gw.train(STALKER))

# 적군 찾기
    def find_target(self, state):
        if len(self.known_enemy_units) > 0: # 발견된 적이 없으면 적군을 찾는다.
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0: # 발견된 건물이 없으면 건물을 찾는다.
            return random.choice(self.known_enemy_structures)
        else: # 그 외의 경우에는 출발점으로 돌아간다.
            return self.enemy_start_locations[0]

# 공격
    async def attack(self):
        if self.units(STALKER).amount > 15:
            for s in self.units(STALKER).idle:
                await self.do(s.attack(self.find_target(self.state)))


        elif self.units(STALKER).amount > 3: # 추적자가 5기 이상이면
            if len(self.known_enemy_units) > 0: # 발견된 적이 없는 상태이면
                for s in self.units(STALKER).idle: # 추적자가 행동을 안하고 있으면
                    await self.do(s.attack(random.choice(self.known_enemy_units))) # 보이는 적을 공격한다.


# run_game: map선택, Bot(종족, SentdeBot 클래스 - 기능 구현), Computer(종족, 난이도) / realtime: 게임속도
run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, SentdeBot()),
    Computer(Race.Terran, Difficulty.Medium)
], realtime=False)
