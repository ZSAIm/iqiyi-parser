function ArrayBuffer(byte_length){  //byte unsigned int
    this.buffer = Array(byte_length);
    this.length = byte_length;
    this.begin = 0;

    for (var i = 0; i < byte_length; i++){
        this.buffer[i] = 0;
    }

}

function BitInversion(bit){
    bit_str = "";
    str = bit.toString();
    for (i in str){
        bit_str += str[i] == "1" ? "0" : "1";
    }
    return bit_str;
}

function IntBitTo32UIntBit(bit){

    if (bit < 0){
        tmp_str = bit.substring(1);
        bit_str = "";
        bit_str = BitInversion(tmp_str);

        tmp_count = bit_str.length;
        bit_str = (parseInt(bit_str, 2)+1).toString(2);
        count = tmp_count - bit_str.length;
        for (var i = 0; i < count; i++){
            bit_str = "0" + bit_str;
        }
        for (var i = 0; 32 - bit_str.length > 0; i++){
            bit_str = "1" + bit_str;
        }
        return bit_str;

    }else{
        var bit_str = bit;
        for (var i = 0; 32 - bit_str.length > 0; i++){
            bit_str = "0" + bit_str;
        }
        return bit_str

    }

}


function Int32Array(ArrayBuffer_Object){


    function set(index, value){

        // console.log(value)
        if (typeof value != "number"){
            for (x in value){
                var bit_str = value[x].toString(2);
                bit_str = IntBitTo32UIntBit(bit_str);
                this.buffer[(index+ this.begin)*4] = parseInt(bit_str.substring(bit_str.length - 8, bit_str.length), 2);
                this.buffer[(index+ this.begin)*4+1] = parseInt(bit_str.substring(bit_str.length - 16, bit_str.length-8), 2);
                this.buffer[(index+ this.begin)*4+2] = parseInt(bit_str.substring(bit_str.length - 24, bit_str.length-16), 2);
                this.buffer[(index+ this.begin)*4+3] = parseInt(bit_str.substring(bit_str.length - 36, bit_str.length-24), 2);
                index ++
            }

            // console.log(this.buffer);
        }else{
            var bit_str = value.toString(2);
            bit_str = IntBitTo32UIntBit(bit_str);
            // console.log(typeof parseInt(bit_str.substring(bit_str.length - 8, bit_str.length), 2));
            this.buffer[(index+ this.begin)*4] = parseInt(bit_str.substring(bit_str.length - 8, bit_str.length), 2);
            this.buffer[(index+ this.begin)*4+1] = parseInt(bit_str.substring(bit_str.length - 16, bit_str.length-8), 2);
            this.buffer[(index+ this.begin)*4+2] = parseInt(bit_str.substring(bit_str.length - 24, bit_str.length-16), 2);
            this.buffer[(index+ this.begin)*4+3] = parseInt(bit_str.substring(bit_str.length - 36, bit_str.length-24), 2);

        }
        // console.log(this.buffer);
        // this.ArrayBuffer_Object[
    }

    function get(index){

        bit_str = "";
        for (var i = 0; i < 4; i++){
            e = this.buffer[(index+ this.begin)*4 + i].toString(2);
            tmp_count = 8 - e.length;
            // console.log(e.length)
            for (var j = 0; j < tmp_count; j++){
                e = "0" + e;
            }
            bit_str = e + bit_str;
        }

        if (bit_str[0] == "1"){ //?????????1???32???
            while (str = bit_str.substring(1), str[0] != "0"){
                bit_str = str;
            }
        }
        if (bit_str[0] != "1"){
            return parseInt(bit_str, 2);
        }
        bit_str = (parseInt(BitInversion(bit_str), 2)+1).toString(2);

        return parseInt("-" + bit_str, 2);


    }

    function subarray(begin, end){
        // new_object = new Int32Array(this.ArrayBuffer_Object);
        // new_object.begin = begin;
        // new_object.length = this.length - begin;
        // return new_object;
        var end = arguments[1] ? arguments[1] : this.length;
        sublist = [];
        for (var i = 0; i < end - begin; i++){
            sublist.push(this.get(begin + i));

        }
        // console.log(sublist);
        return sublist;
    }

    this.ArrayBuffer_Object = ArrayBuffer_Object;
    this.buffer = ArrayBuffer_Object.buffer
    this.begin = 0;
    this.length = this.buffer.length / 4;
    this.set = set;
    this.get = get;
    this.subarray = subarray;

}

function Int8Array(ArrayBuffer_Object){
    function set(index, value){

        if (typeof value != "number"){
            for (x in value){
                var bit_str = value[x].toString(2);
                bit_str = IntBitTo32UIntBit(bit_str);
                this.buffer[index + this.begin] = parseInt(bit_str, 2) & 255;
                index ++
            }

        }else{
            var bit_str = value.toString(2);
            bit_str = IntBitTo32UIntBit(bit_str);
            this.buffer[index+ this.begin] = parseInt(bit_str, 2) & 255;
        }
    }

    function get(index){
        if ((this.buffer[index+ this.begin] & 128) == 0){
            return this.buffer[index + this.begin];
        }
        bit_str = (parseInt(BitInversion(this.buffer[index+ this.begin].toString(2)), 2)+1).toString(2);
        bit_str = parseInt("-" + bit_str, 2);
        return bit_str;
    }

    function subarray(begin, end){

        var end = arguments[1] ? arguments[1] : this.length;
        sublist = [];
        for (var i = 0; i < end - begin; i++){
            sublist.push(this.get(begin + i));

        }
        // console.log(sublist);
        return sublist;

    }

    this.ArrayBuffer_Object = ArrayBuffer_Object;
    this.buffer = ArrayBuffer_Object.buffer;
    this.begin = 0;
    this.length = this.buffer.length;
    this.set = set;
    this.get = get;
    this.subarray = subarray;

}


function Uint8Array(ArrayBuffer_Object){
    function set(index, value){
        if (typeof value != "number"){
            for (x in value){
                this.buffer[index + this.begin] = value[x];
                index ++
            }
        }else{
            this.buffer[index + this.begin] = value;
        }
    }
    function get(index){
        return this.buffer[index + this.begin];
    }
    function subarray(begin, end){
        var end = arguments[1] ? arguments[1] : this.length;
        sublist = [];
        for (var i = 0; i < end - begin; i++){
            sublist.push(this.get(begin + i));

        }
        // console.log(sublist);
        return sublist;

    }

    this.ArrayBuffer_Object = ArrayBuffer_Object;
    this.buffer = ArrayBuffer_Object.buffer;
    this.length = this.buffer.length;
    this.begin = 0;
    this.set = set;
    this.get = get;
    this.subarray = subarray;

}