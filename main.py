import numpy as np

# LRU implementation class
class LRU():
    def __init__(self) -> None:
        self.queue = []
    
    def new(self, page, name = 'pt'):
        self.queue.insert(0, page)
        
    def page_fault(self, table):
        # verify addr that will be removed
        pages = list(table.keys())
        physical_addr = list(table.values())
        removed_page =  self.queue.pop()
        # get page that will be removed 
        idx = pages.index(removed_page)
        addr_available = physical_addr[idx]
        return removed_page, addr_available
    
    def update(self, x) -> None:
        idx = self.queue.index(x)
        self.queue = [x] + self.queue[:idx] + self.queue[idx+1:]

# Second Chance implementation class
class SecondChance():
    def __init__(self) -> None:
        self.queue = []

    def new(self, page):
        self.queue.insert(0, [page, 1])
        
    def get_removed_page(self):
        for value in self.queue:
            p, b = value
            if b == 0:
                self.queue.remove(value)
                return p
            # shift queue
            self.queue = self.queue[1:]
            self.queue.append([p, 0])
        # if there is no 0 bit, return the first
        p = self.queue[0][0]
        del self.queue[0]
        return p

    def page_fault(self, table):
        # verify page that will be removed
        pages = list(table.keys())
        physical_addr = list(table.values())
        removed_page = self.get_removed_page()

        # get index that will be removed
        idx = pages.index(removed_page)
        addr_available = physical_addr[idx]
        return removed_page, addr_available

    def update(self, x):
        for idx, value in enumerate(self.queue):
            p, b = value
            if p == x:
                self.queue[idx] = [p, 1] 
    
class PageTable():
    PAGE_TABLE_SIZE = 64
    def __init__(self, method) -> None:
        self.page_table = {}
        self.disk_op_counter = 0
        self.alg_page_fault = method()
        self.free_mem = self.__gen_virtual_mem()

    def __gen_virtual_mem(self) -> list:
        page_size = 3 * 1024 
        addrs = []
        max_addrs = self.PAGE_TABLE_SIZE
        for i in range(max_addrs):
            addr = i * page_size
            addrs.append(f'0x{addr:05X}')
        return addrs
    
    def search_page_table(self,p):
        x = self.page_table.get(p)
        # page not found at memory
        if x == None:
            self.disk_op_counter+=1
            # in case any frame is available
            if len(self.free_mem) > 0:
                x = self.free_mem.pop() 
                self.page_table[p] = x
                self.alg_page_fault.new(p)
                return x
            else:
                removed_page, addr_available = self.alg_page_fault.page_fault(self.page_table)
                self.alg_page_fault.new(p)
                del self.page_table[removed_page]
                self.page_table[p] = addr_available
                return addr_available
        else:
            self.alg_page_fault.update(p)
            return x

# TLB class
class TLB():
    TLB_SIZE = 16
    def __init__(self, method) -> None:
        self.tlb = {}
        self.hit = 0
        self.miss = 0
        self.alg_page_fault = method()
        self.second_chance = SecondChance()
    
    def display_hits(self):
        print(f'TLB MISS: {self.miss}')
        print(f'TLB HIT: {self.hit}')
        
    def count_tlb_hit(self):
        self.hit+=1

    def count_tlb_miss(self):
        self.miss+=1

    def search_tlb(self, p) -> str:
        f = self.tlb.get(p)
        if f != None:
            self.alg_page_fault.update(p)
        return f
    
    def update(self, p, f):
        if len(self.tlb) == self.TLB_SIZE:
            removed_page, _ = self.alg_page_fault.page_fault(self.tlb)
            del self.tlb[removed_page]
        self.tlb[p] = f 
        self.alg_page_fault.new(p)


# MMU class
class MMU():
    def __init__(self, method) -> None:
        self.tlb = TLB(method=method)
        self.page_table = PageTable(method=method)

    def translate_addr(self, adr) -> list:
        p, d = adr[:5], adr[5:]
        
        # TLB ops
        frame = self.tlb.search_tlb(p)
        if frame == None:
            self.tlb.count_tlb_miss()
            frame = self.page_table.search_page_table(p)
            self.tlb.update(p, frame)
        else:
            self.tlb.count_tlb_hit() 
        return frame, d

# Reading traces
def read_trace(filename):
    with open(filename, 'r') as file:
        txts = file.readlines()
    return np.array([x.split() for x in txts])

traces = read_trace('traces/bzip.trace').T
address = traces[0]

# Instance MMU object
mmu = MMU(method = LRU)

for adr in address:
    p = mmu.translate_addr(adr)

print(f'Operações em disco: {mmu.page_table.disk_op_counter}')
mmu.tlb.display_hits()