def gen_virtual_memory():
    page_size = 4 * 1024 
    addrs = []
    max_addrs = 64
    
    for i in range(max_addrs):
        addr = i * page_size
        addrs.append(f'0x{addr:05X}') 
    return addrs
