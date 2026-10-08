#!/usr/bin/env python3
"""Emulated LoRaWAN end devices -> local MQTT, ChirpStack v4 JSON uplink format.
Same topics and field names as the CQU feed (RAK7204 environmental, soil probe).
VALUES ARE SIMULATED (daily cycle + noise + irrigation events). Disclose this.
Run:  pip install paho-mqtt && python3 lorawan_sim.py [seconds_between_uplinks]
"""
import json, math, random, sys, time, uuid, datetime as dt
import paho.mqtt.client as mqtt
ENV_APP="3abe7286-a458-45a3-b535-f94afe82ff7e"; SOIL_APP="4dcbfc34-d6ef-49c2-99d5-992b20d80fac"
EVERY=float(sys.argv[1]) if len(sys.argv)>1 else 30
c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) if hasattr(mqtt,"CallbackAPIVersion") else mqtt.Client()
c.connect("localhost",1883); c.loop_start()
soil=32.0; fcnt=0
def uplink(app,appname,dev,eui,obj):
    global fcnt; fcnt+=1
    return {"deduplicationId":str(uuid.uuid4()),"time":dt.datetime.utcnow().isoformat()+"Z",
     "deviceInfo":{"tenantName":"CQU","applicationId":app,"applicationName":appname,"deviceName":dev,"devEui":eui},
     "devAddr":"01020304","adr":True,"dr":5,"fCnt":fcnt,"fPort":10,"confirmed":False,
     "rxInfo":[{"gatewayId":"0102030405060708","rssi":-61+random.randint(-6,6),"snr":9.0+random.uniform(-3,2)}],
     "txInfo":{"frequency":923200000,"modulation":{"lora":{"bandwidth":125000,"spreadingFactor":7,"codeRate":"CR_4_5"}}},
     "object":obj}
while True:
    h=(time.time()/3600+10)%24                       # local-ish hour of day
    temp=17+7*math.sin((h-9)/24*2*math.pi)+random.gauss(0,.3)
    hum=max(15,min(98,62-18*math.sin((h-9)/24*2*math.pi)+random.gauss(0,1.5)))
    env={"temperature_7":round(temp,1),"humidity_6":round(hum,1),"barometer_8":round(1012+random.gauss(0,.8),1)}
    soil-=random.uniform(0.05,0.35)*(1+max(0,temp-20)/15)      # drying
    if soil<18 or random.random()<0.004: soil=random.uniform(40,46)  # irrigation event
    sd={"Bat":round(3.62-random.uniform(0,.02),2),"TempC_DS18B20":round(temp-1,1),
        "water_SOIL":round(soil,1),"temp_SOIL":round(temp-3+random.gauss(0,.2),1),"conduct_SOIL":round(180+soil*2+random.gauss(0,5))}
    c.publish(f"application/{ENV_APP}/device/rak7204-sim/event/up",json.dumps(uplink(ENV_APP,"Environmental","rak7204-sim","a84041000181c0aa",env)))
    c.publish(f"application/{SOIL_APP}/device/soil-sim/event/up",json.dumps(uplink(SOIL_APP,"Soil moisture","soil-sim","a84041000181c0bb",sd)))
    print(env,sd,flush=True); time.sleep(EVERY)
