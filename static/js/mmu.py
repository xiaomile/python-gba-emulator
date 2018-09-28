class MemoryView(object):

    def __init__(self,memory,offset):
        #self.inherit()
        self.buffer = memory
        self.view = DataView(self.buffer, offset if type(offset) == type(int) else 0)
        self.mask = memory.byteLength - 1
        self.resetMask()


    def resetMask(self) :
        self.mask8 = self.mask & 0xFFFFFFFF
        self.mask16 = self.mask & 0xFFFFFFFE
        self.mask32 = self.mask & 0xFFFFFFFC

    def load8(self,offset):
        return self.view.getInt8(offset & self.mask8)


    def load16(self,offset):
        # Unaligned 16-bit loads are unpredictable...let's just pretend they work
        return self.view.getInt16(offset & self.mask, true)


    def loadU8(self,offset):
        return self.view.getUint8(offset & self.mask8)


    def loadU16(self,offset):
        # Unaligned 16-bit loads are unpredictable...let's just pretend they work
        return self.view.getUint16(offset & self.mask, true)


    def load32(self,offset):
        # Unaligned 32-bit loads are "rotated" so they make some semblance of sense
        rotate = (offset & 3) << 3
        mem = self.view.getInt32(offset & self.mask32, true)
        return (mem >>rotate) | (mem << (32 - rotate))


    def store8(self,offset, value):
        self.view.setInt8(offset & self.mask8, value);

    def store16(self,offset, value):
        self.view.setInt16(offset & self.mask16, value, true)


    def store32(self,offset, value):
        self.view.setInt32(offset & self.mask32, value, true);


    def invalidatePage(self,address):
        pass

    def replaceData(self,memory, offset):
        self.buffer = memory;
        self.view = DataView(self.buffer, offset if type(offset) == type(int) else 0)
        if self.icache :
            self.icache = bytearray(self.icache.length)
    


class MemoryBlock(MemoryView):
    def __init__(self,size, cacheBits) :
        super(MemoryBlock,self).__init__(ArrayBuffer(size),size)
        self.ICACHE_PAGE_BITS = cacheBits
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1
        self.icache = bytearray(size >> (self.ICACHE_PAGE_BITS + 1))


        #MemoryBlock.prototype = Object.create(MemoryView.prototype);

    def invalidatePage(self,address):
        page = self.icache[(address & self.mask) >> self.ICACHE_PAGE_BITS]
        if page:
            page.invalid = true
    


class ROMView(MemoryView):
    def __init__(self,rom, offset):
        super(ROMView,self).__init__(rom, offset)
        self.ICACHE_PAGE_BITS = 10
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1
        self.icache = bytearray(rom.byteLength >> (self.ICACHE_PAGE_BITS + 1))
        self.mask = 0x01FFFFFF
        self.resetMask()


    #ROMView.prototype = Object.create(MemoryView.prototype);

    def store8(self,offset, value):
        pass

    def store16(self,offset, value):
        if offset < 0xCA and offset >= 0xC4:
            if not self.gpio:
                self.gpio = self.mmu.allocGPIO(self)
        
            self.gpio.store16(offset, value)
    


    def store32(self,offset, value):
        if offset < 0xCA and offset >= 0xC4:
            if not self.gpio:
                self.gpio = self.mmu.allocGPIO(self);
        
            self.gpio.store32(offset, value);
    


class BIOSView(MemoryView):
    def __init__(self,rom, offset):
        super(BIOSView,self).__init__(rom, offset)
        self.ICACHE_PAGE_BITS = 16
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1
        self.icache = bytearray(1)


    #BIOSView.prototype = Object.create(MemoryView.prototype);

    def load8(self,offset):
        if offset >= len(self.buffer):
            return -1
    
        return self.view.getInt8(offset)


    def load16(self,offset):
        if offset >= len(self.buffer):
            return -1
    
        return self.view.getInt16(offset, true)


    def loadU8(self,offset):
        if offset >= len(self.buffer):
            return -1

        return self.view.getUint8(offset)


    def loadU16(self,offset):
        if offset >= len(self.buffer):
            return -1
    
        return self.view.getUint16(offset, true)


    def load32(self,offset):
        if (offset >= len(self.buffer)):
            return -1
    
        return self.view.getInt32(offset, true)


    def store8(self,offset, value):
        pass

    def store16(self,offset, value):
        pass

    def store32(self,offset, value):
        pass

class BadMemory():
    def __init__(self,mmu, cpu):
        self.inherit()
        self.cpu = cpu
        self.mmu = mmu


    def load8(self,offset) :
        return self.mmu.load8(self.cpu.gprs[self.cpu.PC] - self.cpu.instructionWidth + (offset & 0x3))


    def load16(self,offset) :
        return self.mmu.load16(self.cpu.gprs[self.cpu.PC] - self.cpu.instructionWidth + (offset & 0x2))


    def loadU8(self,offset) :
        return self.mmu.loadU8(self.cpu.gprs[self.cpu.PC] - self.cpu.instructionWidth + (offset & 0x3));


    def loadU16(self,offset) :
        return self.mmu.loadU16(self.cpu.gprs[self.cpu.PC] - self.cpu.instructionWidth + (offset & 0x2));

    def load32(self,offset) :
        if self.cpu.execMode == self.cpu.MODE_ARM :
            return self.mmu.load32(self.cpu.gprs[self.cpu.gprs.PC] - self.cpu.instructionWidth)
        else :
            halfword = self.mmu.loadU16(self.cpu.gprs[self.cpu.PC] - self.cpu.instructionWidth)
            return halfword | (halfword << 16)
    


    def store8(self,offset, value):
        pass

    def store16(self,offset, value):
        pass
    def store32(self,offset, value):
        pass

    def invalidatePage(self,address):
        pass

class getObject(object):
    def __init__(self):
        pass

class GameBoyAdvanceMMU():
    #self.inherit();
    def __init__(self):
        self.REGION_BIOS = 0x0
        self.REGION_WORKING_RAM = 0x2
        self.REGION_WORKING_IRAM = 0x3
        self.REGION_IO = 0x4
        self.REGION_PALETTE_RAM = 0x5
        self.REGION_VRAM = 0x6
        self.REGION_OAM = 0x7
        self.REGION_CART0 = 0x8
        self.REGION_CART1 = 0xA
        self.REGION_CART2 = 0xC
        self.REGION_CART_SRAM = 0xE

        self.BASE_BIOS = 0x00000000
        self.BASE_WORKING_RAM = 0x02000000
        self.BASE_WORKING_IRAM = 0x03000000
        self.BASE_IO = 0x04000000
        self.BASE_PALETTE_RAM = 0x05000000
        self.BASE_VRAM = 0x06000000
        self.BASE_OAM = 0x07000000
        self.BASE_CART0 = 0x08000000
        self.BASE_CART1 = 0x0A000000
        self.BASE_CART2 = 0x0C000000
        self.BASE_CART_SRAM = 0x0E000000

        self.BASE_MASK = 0x0F000000
        self.BASE_OFFSET = 24
        self.OFFSET_MASK = 0x00FFFFFF

        self.SIZE_BIOS = 0x00004000
        self.SIZE_WORKING_RAM = 0x00040000
        self.SIZE_WORKING_IRAM = 0x00008000
        self.SIZE_IO = 0x00000400
        self.SIZE_PALETTE_RAM = 0x00000400
        self.SIZE_VRAM = 0x00018000
        self.SIZE_OAM = 0x00000400
        self.SIZE_CART0 = 0x02000000
        self.SIZE_CART1 = 0x02000000
        self.SIZE_CART2 = 0x02000000
        self.SIZE_CART_SRAM = 0x00008000
        self.SIZE_CART_FLASH512 = 0x00010000
        self.SIZE_CART_FLASH1M = 0x00020000
        self.SIZE_CART_EEPROM = 0x00002000

        self.DMA_TIMING_NOW = 0
        self.DMA_TIMING_VBLANK = 1
        self.DMA_TIMING_HBLANK = 2
        self.DMA_TIMING_CUSTOM = 3

        self.DMA_INCREMENT = 0
        self.DMA_DECREMENT = 1
        self.DMA_FIXED = 2
        self.DMA_INCREMENT_RELOAD = 3

        self.DMA_OFFSET = [ 1, -1, 0, 1 ]

        self.WAITSTATES = [ 0, 0, 2, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4 ]
        self.WAITSTATES_32 = [ 0, 0, 5, 0, 0, 1, 0, 1, 7, 7, 9, 9, 13, 13, 8 ]
        self.WAITSTATES_SEQ = [ 0, 0, 2, 0, 0, 0, 0, 0, 2, 2, 4, 4, 8, 8, 4 ]
        self.WAITSTATES_SEQ_32 = [ 0, 0, 5, 0, 0, 1, 0, 1, 5, 5, 9, 9, 17, 17, 8 ]
        self.NULLWAIT = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]

        for i in  range(15,256):
            self.WAITSTATES[i] = 0
            self.WAITSTATES_32[i] = 0
            self.WAITSTATES_SEQ[i] = 0
            self.WAITSTATES_SEQ_32[i] = 0
            self.NULLWAIT[i] = 0
    

        self.ROM_WS = [ 4, 3, 2, 8 ]
        self.ROM_WS_SEQ = [
            [ 2, 1 ],
            [ 4, 1 ],
            [ 8, 1 ]
        ]

        self.ICACHE_PAGE_BITS = 8
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1

        self.bios = None


    def mmap(self,region, makeobject) :
        self.memory[region] = makeobject


    def clear(self):
        self.badMemory = BadMemory(self, self.cpu);
        self.memory = [
            self.bios,
            self.badMemory, # Unused
            MemoryBlock(self.SIZE_WORKING_RAM, 9),
            MemoryBlock(self.SIZE_WORKING_IRAM, 7),
            None, # self is owned by GameBoyAdvanceIO
            None, # self is owned by GameBoyAdvancePalette
            None, # self is owned by GameBoyAdvanceVRAM
            None, # self is owned by GameBoyAdvanceOAM
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory # Unused
        ]
        for i in range(16,256):
            self.memory.insert(i,self.badMemory)
    

        self.waitstates = self.WAITSTATES[0]
        self.waitstatesSeq = self.WAITSTATES_SEQ[0]
        self.waitstates32 = self.WAITSTATES_32[0]
        self.waitstatesSeq32 = self.WAITSTATES_SEQ_32[0]
        self.waitstatesPrefetch = self.WAITSTATES_SEQ[0]
        self.waitstatesPrefetch32 = self.WAITSTATES_SEQ_32[0]

        self.cart = None
        self.save = None

        self.DMA_REGISTER = [
        self.core.io.DMA0CNT_HI >> 1,
        self.core.io.DMA1CNT_HI >> 1,
        self.core.io.DMA2CNT_HI >> 1,
        self.core.io.DMA3CNT_HI >> 1
        ]


    def freeze(self):
        return {
            'ram': Serializer.prefix(self.memory[self.REGION_WORKING_RAM].buffer),
            'iram': Serializer.prefix(self.memory[self.REGION_WORKING_IRAM].buffer),
        }
    

    def defrost(self,frost):
        self.memory[self.REGION_WORKING_RAM].replaceData(frost.ram)
        self.memory[self.REGION_WORKING_IRAM].replaceData(frost.iram)


    def loadBios(self,bios, real):
        self.bios = BIOSView(bios)
        self.bios.real = real


    def loadRom(self,rom, process):
        cart = getObject()
        cart.title = None
        cart.code = None
        cart.maker = None
        cart.memory = rom
        cart.saveType = None
        

        lo = ROMView(rom)
        if lo.view.getUint8(0xB2) != 0x96:
            # Not a valid ROM
            return None
    
        lo.mmu = self # Needed for GPIO
        self.memory[self.REGION_CART0] = lo
        self.memory[self.REGION_CART1] = lo
        self.memory[self.REGION_CART2] = lo

        if rom.byteLength > 0x01000000:
            hi = ROMView(rom, 0x01000000);
            self.memory[self.REGION_CART0 + 1] = hi
            self.memory[self.REGION_CART1 + 1] = hi
            self.memory[self.REGION_CART2 + 1] = hi
    

        if process:
            name = '';
            for i in  range(0,12):
                c = lo.loadU8(i + 0xA0)
                if not c:
                    break
            
                name += chr(c);
        
            cart.title = name;

            code = '';
            for i in range(0,4):
                c = lo.loadU8(i + 0xAC)
                if not c:
                    break
            
                code += chr(c);
        
            cart.code = code;

            maker = '';
            for i in range(0,2):
                c = lo.loadU8(i + 0xB0)
                if not c:
                    break
                
                maker += chr(c)
            
            cart.maker = maker

            # Find savedata type
            state = ''
            nextcode = ''
            terminal = False
            for i  in range(0xE4,rom.byteLength):
                if not terminal:
                    break
                nextcode = chr(lo.loadU8(i))
                state += nextcode
                if state == 'F':
                    pass
                elif state == 'FL':
                    pass
                elif state == 'FLA':
                    pass
                elif state == 'FLAS':
                    pass
                elif state == 'FLASH':
                    pass
                elif state == 'FLASH_':
                    pass
                elif state == 'FLASH5':
                    pass
                elif state == 'FLASH51':
                    pass
                elif state == 'FLASH512':
                    pass
                elif state == 'FLASH512_':
                    pass
                elif state == 'FLASH1':
                    pass
                elif state == 'FLASH1M':
                    pass
                elif state == 'FLASH1M_':
                    pass
                elif state == 'S':
                    pass
                elif state == 'SR':
                    pass
                elif state == 'SRA':
                    pass
                elif state == 'SRAM':
                    pass
                elif state == 'SRAM_':
                    pass
                elif state == 'E':
                    pass
                elif state == 'EE':
                    pass
                elif state == 'EEP':
                    pass
                elif state == 'EEPR':
                    pass
                elif state == 'EEPRO':
                    pass
                elif state == 'EEPROM':
                    pass
                elif state == 'EEPROM_':
                    break
                elif state == 'FLASH_V':
                    pass
                elif state == 'FLASH512_V':
                    pass
                elif state == 'FLASH1M_V':
                    pass
                elif state == 'SRAM_V':
                    pass
                elif state == 'EEPROM_V':
                    terminal = True
                    break
                else:
                    state = nextcode
                    break
            
        
            if terminal:
                cart.saveType = state
                if state == 'FLASH_V':
                    pass
                elif state == 'FLASH512_V':
                    self.save = self.memory[self.REGION_CART_SRAM] = FlashSavedata(self.SIZE_CART_FLASH512)
                    #break
                elif state == 'FLASH1M_V':
                    self.save = self.memory[self.REGION_CART_SRAM] = FlashSavedata(self.SIZE_CART_FLASH1M)
                    #break
                elif state == 'SRAM_V':
                    self.save = self.memory[self.REGION_CART_SRAM] = SRAMSavedata(self.SIZE_CART_SRAM)
                    #break
                elif state == 'EEPROM_V':
                    self.save = self.memory[self.REGION_CART2 + 1] = EEPROMSavedata(self.SIZE_CART_EEPROM, self)
                    #break
            
        
            if not self.save:
                # Assume we have SRAM
                self.save = self.memory[self.REGION_CART_SRAM] = SRAMSavedata(self.SIZE_CART_SRAM);
        
    

        self.cart = cart
        return cart


    def loadSavedata(self,save):
        self.save.replaceData(save)


    def load8(self,offset):
        return self.memory[offset >> self.BASE_OFFSET].load8(offset & 0x00FFFFFF)


    def load16(self,offset):
        return self.memory[offset >> self.BASE_OFFSET].load16(offset & 0x00FFFFFF)


    def load32(self,offset):
        return self.memory[offset >> self.BASE_OFFSET].load32(offset & 0x00FFFFFF);


    def loadU8(self,offset):
        return self.memory[offset >> self.BASE_OFFSET].loadU8(offset & 0x00FFFFFF);


    def loadU16(self,offset):
        return self.memory[offset >> self.BASE_OFFSET].loadU16(offset & 0x00FFFFFF);


    def store8(self,offset, value):
        maskedOffset = offset & 0x00FFFFFF
        memory = self.memory[offset >> self.BASE_OFFSET]
        memory.store8(maskedOffset, value)
        memory.invalidatePage(maskedOffset)


    def store16(self,offset, value):
        maskedOffset = offset & 0x00FFFFFE
        memory = self.memory[offset >> self.BASE_OFFSET]
        memory.store16(maskedOffset, value)
        memory.invalidatePage(maskedOffset)


    def store32(self,offset, value):
        maskedOffset = offset & 0x00FFFFFC
        memory = self.memory[offset >> self.BASE_OFFSET]
        memory.store32(maskedOffset, value)
        memory.invalidatePage(maskedOffset)
        memory.invalidatePage(maskedOffset + 2)


    def waitPrefetch(self,memory):
        self.cpu.cycles += 1 + self.waitstatesPrefetch[memory >> self.BASE_OFFSET]


    def waitPrefetch32(self,memory) :
        self.cpu.cycles += 1 + self.waitstatesPrefetch32[memory >> self.BASE_OFFSET]


    def wait(self,memory):
        self.cpu.cycles += 1 + self.waitstates[memory >> self.BASE_OFFSET]


    def wait32(self,memory):
        self.cpu.cycles += 1 + self.waitstates32[memory >> self.BASE_OFFSET]


    def waitSeq(self,memory) :
        self.cpu.cycles += 1 + self.waitstatesSeq[memory >> self.BASE_OFFSET]


    def waitSeq32(self,memory) :
        self.cpu.cycles += 1 + self.waitstatesSeq32[memory >> self.BASE_OFFSET]


    def waitMul(rs) :
        if ((rs & 0xFFFFFF00 == 0xFFFFFF00) or not (rs & 0xFFFFFF00)) :
            self.cpu.cycles += 1
        elif ((rs & 0xFFFF0000 == 0xFFFF0000) or not (rs & 0xFFFF0000)) :
            self.cpu.cycles += 2
        elif ((rs & 0xFF000000 == 0xFF000000) or not (rs & 0xFF000000)) :
            self.cpu.cycles += 3
        else :
            self.cpu.cycles += 4
    


    def waitMulti32(self,memory, seq) :
        self.cpu.cycles += 1 + self.waitstates32[memory >> self.BASE_OFFSET]
        self.cpu.cycles += (1 + self.waitstatesSeq32[memory >> self.BASE_OFFSET]) * (seq - 1)


    def addressToPage(self,region, address):
        return address >> self.memory[region].ICACHE_PAGE_BITS


    def accessPage(self,region, pageId) :
        memory = self.memory[region]
        page = memory.icache[pageId]
        if (not page or page.invalid) :
            page = getObject()
            page.thumb = bytearray(1 << (memory.ICACHE_PAGE_BITS))
            page.arm= bytearray(1 << memory.ICACHE_PAGE_BITS - 1)
            page.invalid = False
        
            memory.icache[pageId] = page;
    
        return page


    def scheduleDma(self,number, info) :
        if info.timing == self.DMA_TIMING_NOW:
            self.serviceDma(number, info)
        elif info.timing == self.DMA_TIMING_HBLANK:
            # Handled implicitly
            pass
        elif info.timing == self.DMA_TIMING_VBLANK:
            # Handled implicitly
            pass
        elif info.timing == self.DMA_TIMING_CUSTOM:
            if number == 0:
                self.core.WARN('Discarding invalid DMA0 scheduling')
            
            elif number == 1:
                pass
            elif number == 2:
                self.cpu.irq.audio.scheduleFIFODma(number, info)
        
            elif number == 3:
                self.cpu.irq.video.scheduleVCaptureDma(dma, info)
            
        


    def runHblankDmas(self) :
        
        for i in range(0,self.cpu.irq.dma.length) :
            dma = self.cpu.irq.dma[i]
            if (dma.enable and dma.timing == self.DMA_TIMING_HBLANK) :
                self.serviceDma(i, dma)
        
    


    def runVblankDmas(self) :
    
        for i in range(0,self.cpu.irq.dma.length) :
            dma = self.cpu.irq.dma[i]
            if (dma.enable and dma.timing == self.DMA_TIMING_VBLANK) :
                self.serviceDma(i, dma)
        
    


    def serviceDma(self,number, info) :
        if (not info.enable) :
            # There was a DMA scheduled that got canceled
            return None
    

        width = info.width
        sourceOffset = self.DMA_OFFSET[info.srcControl] * width
        destOffset = self.DMA_OFFSET[info.dstControl] * width
        wordsRemaining = info.nextCount
        source = info.nextSource & self.OFFSET_MASK
        dest = info.nextDest & self.OFFSET_MASK
        sourceRegion = info.nextSource >> self.BASE_OFFSET
        destRegion = info.nextDest >> self.BASE_OFFSET
        sourceBlock = self.memory[sourceRegion]
        destBlock = self.memory[destRegion]
        sourceView = None
        destView = None
        sourceMask = 0xFFFFFFFF
        destMask = 0xFFFFFFFF
        

        if (destBlock.ICACHE_PAGE_BITS) :
            endPage = (dest + wordsRemaining * width) >> destBlock.ICACHE_PAGE_BITS;
            for i in range(dest >> destBlock.ICACHE_PAGE_BITS,endPage) :
                destBlock.invalidatePage(i << destBlock.ICACHE_PAGE_BITS)
        
    

        if (destRegion == self.REGION_WORKING_RAM or destRegion == self.REGION_WORKING_IRAM) :
            destView = destBlock.view
            destMask = destBlock.mask
    

        if (sourceRegion == self.REGION_WORKING_RAM or sourceRegion == self.REGION_WORKING_IRAM or sourceRegion == self.REGION_CART0 or sourceRegion == self.REGION_CART1) :
            sourceView = sourceBlock.view;
            sourceMask = sourceBlock.mask;
    

        if (sourceBlock and destBlock) :
            if (sourceView and destView) :
                if (width == 4) :
                    source &= 0xFFFFFFFC
                    dest &= 0xFFFFFFFC
                    wordsRemaining -= 1
                    while (wordsRemaining) :
                        word = sourceView.getInt32(source & sourceMask)
                        destView.setInt32(dest & destMask, word)
                        source += sourceOffset
                        dest += destOffset
                        wordsRemaining -= 1
                
                else:
                    wordsRemaining -= 1
                    while (wordsRemaining) :
                        word = sourceView.getUint16(source & sourceMask)
                        destView.setUint16(dest & destMask, word)
                        source += sourceOffset
                        dest += destOffset
                        wordsRemaining -= 1
                
            
            elif (sourceView) :
                if (width == 4) :
                    source &= 0xFFFFFFFC
                    dest &= 0xFFFFFFFC
                    wordsRemaining -= 1
                    while (wordsRemaining) :
                        word = sourceView.getInt32(source & sourceMask, true)
                        destBlock.store32(dest, word)
                        source += sourceOffset
                        dest += destOffset
                        wordsRemaining -= 1
                
                else :
                    wordsRemaining -= 1
                    while (wordsRemaining) :
                        word = sourceView.getUint16(source & sourceMask, true)
                        destBlock.store16(dest, word)
                        source += sourceOffset
                        dest += destOffset
                        wordsRemaining -= 1
                
            
            else :
                if (width == 4) :
                    source &= 0xFFFFFFFC
                    dest &= 0xFFFFFFFC
                    wordsRemaining -= 1
                    while (wordsRemaining) :
                        word = sourceBlock.load32(source)
                        destBlock.store32(dest, word)
                        source += sourceOffset
                        dest += destOffset
                        wordsRemaining -= 1
                
                else :
                    wordsRemaining -= 1
                    while (wordsRemaining) :
                        word = sourceBlock.loadU16(source)
                        destBlock.store16(dest, word)
                        source += sourceOffset
                        dest += destOffset
                        wordsRemaining -= 1
                
            
        
        else:
            self.core.WARN('Invalid DMA');
    

        if (info.doIrq) :
            info.nextIRQ = self.cpu.cycles + 2;
            info.nextIRQ += (self.waitstates32[sourceRegion] + self.waitstates32[destRegion] if width == 4 else self.waitstates[sourceRegion] + self.waitstates[destRegion])
            info.nextIRQ += (info.count - 1) * (self.waitstatesSeq32[sourceRegion] + self.waitstatesSeq32[destRegion] if width == 4 else self.waitstatesSeq[sourceRegion] + self.waitstatesSeq[destRegion])
    

        info.nextSource = source | (sourceRegion << self.BASE_OFFSET);
        info.nextDest = dest | (destRegion << self.BASE_OFFSET);
        info.nextCount = wordsRemaining;

        if (not info.repeat) :
            info.enable = False

            # Clear the enable bit in memory
            io = self.memory[self.REGION_IO];
            io.registers[self.DMA_REGISTER[number]] &= 0x7FE0
        else :
            info.nextCount = info.count
            if (info.dstControl == self.DMA_INCREMENT_RELOAD) :
                info.nextDest = info.dest
        
            self.scheduleDma(number, info)
    


    def adjustTimings(self,word) :
        sram = word & 0x0003
        ws0 = (word & 0x000C) >> 2
        ws0seq = (word & 0x0010) >> 4
        ws1 = (word & 0x0060) >> 5
        ws1seq = (word & 0x0080) >> 7
        ws2 = (word & 0x0300) >> 8
        ws2seq = (word & 0x0400) >> 10
        prefetch = word & 0x4000

        self.waitstates[self.REGION_CART_SRAM] = self.ROM_WS[sram]
        self.waitstatesSeq[self.REGION_CART_SRAM] = self.ROM_WS[sram]
        self.waitstates32[self.REGION_CART_SRAM] = self.ROM_WS[sram]
        self.waitstatesSeq32[self.REGION_CART_SRAM] = self.ROM_WS[sram]

        self.waitstates[self.REGION_CART0] = self.waitstates[self.REGION_CART0 + 1] = self.ROM_WS[ws0]
        self.waitstates[self.REGION_CART1] = self.waitstates[self.REGION_CART1 + 1] = self.ROM_WS[ws1]
        self.waitstates[self.REGION_CART2] = self.waitstates[self.REGION_CART2 + 1] = self.ROM_WS[ws2]

        self.waitstatesSeq[self.REGION_CART0] = self.waitstatesSeq[self.REGION_CART0 + 1] = self.ROM_WS_SEQ[0][ws0seq]
        self.waitstatesSeq[self.REGION_CART1] = self.waitstatesSeq[self.REGION_CART1 + 1] = self.ROM_WS_SEQ[1][ws1seq]
        self.waitstatesSeq[self.REGION_CART2] = self.waitstatesSeq[self.REGION_CART2 + 1] = self.ROM_WS_SEQ[2][ws2seq]

        self.waitstates32[self.REGION_CART0] = self.waitstates32[self.REGION_CART0 + 1] = self.waitstates[self.REGION_CART0] + 1 + self.waitstatesSeq[self.REGION_CART0]
        self.waitstates32[self.REGION_CART1] = self.waitstates32[self.REGION_CART1 + 1] = self.waitstates[self.REGION_CART1] + 1 + self.waitstatesSeq[self.REGION_CART1]
        self.waitstates32[self.REGION_CART2] = self.waitstates32[self.REGION_CART2 + 1] = self.waitstates[self.REGION_CART2] + 1 + self.waitstatesSeq[self.REGION_CART2]

        self.waitstatesSeq32[self.REGION_CART0] = self.waitstatesSeq32[self.REGION_CART0 + 1] = 2 * self.waitstatesSeq[self.REGION_CART0] + 1
        self.waitstatesSeq32[self.REGION_CART1] = self.waitstatesSeq32[self.REGION_CART1 + 1] = 2 * self.waitstatesSeq[self.REGION_CART1] + 1
        self.waitstatesSeq32[self.REGION_CART2] = self.waitstatesSeq32[self.REGION_CART2 + 1] = 2 * self.waitstatesSeq[self.REGION_CART2] + 1

        if (prefetch) :
            self.waitstatesPrefetch[self.REGION_CART0] = self.waitstatesPrefetch[self.REGION_CART0 + 1] = 0
            self.waitstatesPrefetch[self.REGION_CART1] = self.waitstatesPrefetch[self.REGION_CART1 + 1] = 0
            self.waitstatesPrefetch[self.REGION_CART2] = self.waitstatesPrefetch[self.REGION_CART2 + 1] = 0

            self.waitstatesPrefetch32[self.REGION_CART0] = self.waitstatesPrefetch32[self.REGION_CART0 + 1] = 0
            self.waitstatesPrefetch32[self.REGION_CART1] = self.waitstatesPrefetch32[self.REGION_CART1 + 1] = 0
            self.waitstatesPrefetch32[self.REGION_CART2] = self.waitstatesPrefetch32[self.REGION_CART2 + 1] = 0
        else: 
            self.waitstatesPrefetch[self.REGION_CART0] = self.waitstatesPrefetch[self.REGION_CART0 + 1] = self.waitstatesSeq[self.REGION_CART0]
            self.waitstatesPrefetch[self.REGION_CART1] = self.waitstatesPrefetch[self.REGION_CART1 + 1] = self.waitstatesSeq[self.REGION_CART1]
            self.waitstatesPrefetch[self.REGION_CART2] = self.waitstatesPrefetch[self.REGION_CART2 + 1] = self.waitstatesSeq[self.REGION_CART2]

            self.waitstatesPrefetch32[self.REGION_CART0] = self.waitstatesPrefetch32[self.REGION_CART0 + 1] = self.waitstatesSeq32[self.REGION_CART0]
            self.waitstatesPrefetch32[self.REGION_CART1] = self.waitstatesPrefetch32[self.REGION_CART1 + 1] = self.waitstatesSeq32[self.REGION_CART1]
            self.waitstatesPrefetch32[self.REGION_CART2] = self.waitstatesPrefetch32[self.REGION_CART2 + 1] = self.waitstatesSeq32[self.REGION_CART2]
    


    def saveNeedsFlush(self) :
        return self.save.writePending

    def flushSave(self) :
        self.save.writePending = False


    def allocGPIO(self,rom) :
        return GameBoyAdvanceGPIO(self.core, rom)

