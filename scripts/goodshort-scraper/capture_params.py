"""
Run Frida and capture output properly - v2 with chunked output
"""
import frida
import sys
import time

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'])
    elif message['type'] == 'error':
        print(f"[ERROR] {message['stack']}")

script_code = """
setTimeout(function() {
    Java.perform(function() {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');
        
        var ts = '1769855063192';
        var path = '/home/index';
        var gaid = AppUtils.getGAID();
        var androidId = AppUtils.getAndroidID();
        var userToken = SpData.getUserToken();
        var pkna = AppUtils.getPkna();
        
        send('=== PARAMETERS ===');
        send('path: ' + path);
        send('timestamp: ' + ts);
        send('gaid: ' + gaid);
        send('androidId: ' + androidId);
        send('userToken_length: ' + userToken.length);
        send('userToken_part1: ' + userToken.substring(0, 100));
        send('userToken_part2: ' + userToken.substring(100));
        send('pkna: ' + pkna);
        send('');
        
        // Build input string  
        var input = path + ts + gaid + androidId + userToken + '' + pkna;
        send('=== INPUT STRING ===');
        send('input_length: ' + input.length);
        send('');
        
        // Get sign
        var sign = AppUtils.getSign(ts, path);
        send('=== APP SIGN ===');
        send('sign_length: ' + sign.length);
        send('sign_part1: ' + sign.substring(0, 170));
        send('sign_part2: ' + sign.substring(170));
        send('');
        send('=== DONE ===');
    });
}, 3000);
"""

def main():
    device = frida.get_usb_device()
    
    print("Spawning app...")
    pid = device.spawn(['com.newreading.goodreels'])
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    device.resume(pid)
    
    print("Waiting for output...")
    time.sleep(10)
    
    print("\\n=== Script complete ===")

if __name__ == '__main__':
    main()
