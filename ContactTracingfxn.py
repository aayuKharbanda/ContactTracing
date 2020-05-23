#the user must provide a list of all json files to be dealt with
# all_file_names = ['hamim.json','swaprava.json','guddu.json']
# all_infected = ['guddu']
# levels = 4

def ContactTracing(all_file_names,all_infected,levels):
    new_infected = []
    index_dict = {}
    num_intersect = {}
    dur_intersect = {}
    level_intersect = {}
    infected_score = {}
    for x in all_file_names:
        temp = x.split('.')
        temp = str(temp[0])
        if temp in all_infected:
            index_dict[temp] = 1
        else:
            index_dict[temp] = -1
    # print(index_dict)   
    for x in all_infected:
        num_intersect[x] = 0
        dur_intersect[x] = 0
        level_intersect[x] = 1
        infected_score[x] = 1

    import matplotlib.pyplot as plt

    all_id = []
    N = len(all_file_names)
    combined = []
    combined.append(['id1','id2','Latitude','Longitude','StartTime','EndTime','conf_1','conf_2','net_conf'])
    import time , csv
    start_time = time.time()
    import pandas as pd
    import datetime
    import json
    import os

    #all parameters that can be managed
    r_lat = 0.0005
    r_lng = 0.0005
    indi_confi = 50
    neg_confi = 90
    confi = 60
    #quantity in meters to seperate activity points
    unit = 500
    #quantity in mili sec to seperate activity points
    t_unit = 60000*5
    #grace for activity points
    grace = 60000*5

    from math import radians, cos, sin, asin, sqrt 
    def findLen2(lat1, lat2, lon1, lon2): 
        
        lat1 = (lat1*1.0)/10000000
        lon1 = (lon1*1.0)/10000000
        lat2 = (lat2*1.0)/10000000
        lon2 = (lon2*1.0)/10000000
        lon1 = radians(lon1)
        lon2 = radians(lon2) 
        lat1 = radians(lat1) 
        lat2 = radians(lat2) 

        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

        c = 2 * asin(sqrt(a)) 

        # Radius of earth in kilometers. Use 3956 for miles 
        r = 6371

        # calculate the result 
        return(c * r) 


    def entrymaker(latitude,longitude,idn,start,end,confidence):
            
        latitude = (latitude*1.0)/10000000
        longitude = (longitude*1.0)/10000000
        entry = []
        entry.append(idn)
        
        entry.append(latitude)
        entry.append(longitude)
        entry.append((start))
        entry.append((end))
        entry.append(confidence)
        return entry
    

    def dynamic(x,final,idn):
        start = int(x['duration']['startTimestampMs'])
        end = int(x['duration']['endTimestampMs'])
        confidence = -1
        seg = 1
        dynamiclat = []
        dynamiclong = []
        dynamiclat.append(x['startLocation']['latitudeE7'])
        dynamiclong.append(x['startLocation']['longitudeE7'])
        
        
        
            
        
        if('waypointPath' in x.keys()):
            for y in x['waypointPath']['waypoints']:
                if('latitudeE7' in y.keys()):
                    dynamiclat.append(y['latitudeE7'])
                    dynamiclong.append(y['longitudeE7'])
                else:
                    
                    dynamiclat.append(y['latE7'])
                    dynamiclong.append(y['lngE7'])
                
        if('simplifiedRawPath' in x.keys()):
            for y in x['simplifiedRawPath']['points']:
                if('latitudeE7' in y.keys()):
                    
                    n_lat = (y['latitudeE7'])
                    n_long = (y['longitudeE7'])
                    t = int((y['timestampMs']))
                else:
                    n_lat = (y['latE7'])
                    n_long = (y['lngE7'])
                    t = int(y['timestampMs'])
                final.append(entrymaker(n_lat,n_long,idn,t -300000 ,t + 300000,confidence))
                    
    
        dynamiclat.append(x['endLocation']['latitudeE7'])
        dynamiclong.append(x['endLocation']['longitudeE7'])
        

        
        distance = 0
        for i in range(len(dynamiclat)-1):
            lat1 = dynamiclat[i]
            lat2 = dynamiclat[i+1]
            long1 = dynamiclong[i]
            long2 = dynamiclong[i+1]
            distance += findLen2(lat1,lat2,long1,long2)
            
        
        distance = distance*1000
        time = (end - start)
        time = time

        speed = distance/time


        dt = time/t_unit
        dl = distance/unit
        temp = min(dt,dl)
    #     temp = dl
        totalseg = max(1,int(temp))

        gap = int(time/totalseg)

        index = 0
        new_long = []
        new_lat = []
        new_time = []
        newstart = start
        for i in range(0,len(dynamiclat)-1):
            dx = 0
            dy = 0
            lat1 = dynamiclat[i]
            lat2 = dynamiclat[i+1]
            long1 = dynamiclong[i]
            long2 = dynamiclong[i+1]

            temp = findLen2(lat1,lat2,long1,long2)*1000
            seg = max(1,int(totalseg * temp/(distance)))

            dx = (lat2 - lat1) /seg
            dy = (long2 - long1)/seg


            for j in range(seg):
                new_lat.append(lat1 + dx*j)
                new_long.append(long1 + dy*j)

                new_time.append(newstart + gap*index) 
                newstart +=  gap*index
                index +=1
        
        final.append(entrymaker(dynamiclat[0],dynamiclong[0],idn,start,min(end,start + gap)+grace,confidence))
        for i in range(1,len(new_lat)):
            final.append(entrymaker(new_lat[i],new_long[i],'active',new_time[i]-grace,min(end,new_time[i] + gap)+grace,confidence))
            
        final.append(entrymaker(dynamiclat[-1],dynamiclong[-1],idn,new_time[-1]-grace,end,confidence))
        

    def extract():
        for file in all_file_names :
            jasonName = file
            outName= jasonName.split('.')
            outName = outName[0]
            idn = outName
            print('working with ' + outName)
            outName = outName + '_out.csv'


            with open(jasonName) as json_file :
                data = json.load(json_file)

                final = []

                for pv in data['timelineObjects'] :
                    latitude = 0
                    longitude = 0
                    confidence = 0
                    start = 0
                    end = 0

                    for x in pv.values() :
                        all_keys = list( x.keys())
    #                     print(all_keys)
                        if((all_keys[0]=='startLocation') ):

                            dynamic(x,final,idn)
                            continue

                        
                        if('latitudeE7' in x['location'] ):
                            latitude = x['location']['latitudeE7']
                            longitude = x['location']['longitudeE7']
                        if('latE7' in x['location'] )  :
                            latitude = x['location']['latE7']
                            longitude = x['location']['lngE7']

                        confidence = x['location']['locationConfidence']
                        start = int(x['duration']['startTimestampMs'])
                        end = int(x['duration']['endTimestampMs'])
                        if(confidence >= indi_confi):
                            final.append(entrymaker(latitude,longitude,idn,start,end,confidence))
                        
                            
                        if 'otherCandidateLocations' in x.keys() :
                            for y in x['otherCandidateLocations']:
                                latitude = y['latitudeE7']
                                longitude = y['longitudeE7']
                                confidence = y['locationConfidence']
                                if(confidence >= indi_confi):
                                        final.append(entrymaker(latitude,longitude,idn,start,end,confidence))
                                        
    #             with open(outName, "w", newline="") as f:
    #                         writer = csv.writer(f)
    #                         writer.writerows(final)                
                                

                all_id.append(final)


    
        
    def intersect(i):
        
    #     for i in range(len(all_id)-1):
    #         for j in range(i+1,len(all_id)):
    #     for i in range(len(all_id)-1):
        new_infected = []

        for j in range(0,len(all_id)):
            count = 0
            durat = 0
            scr = 0
            if(j==i):
                continue
            output=[]
            output.append(['id1','id2','Latitude','Longitude','StartTime','EndTime','conf_1','conf_2','net_conf'])
            id1 = all_id[i][0][0]
    #             print(id1)
            id2 = all_id[j][0][0]
            if(id2 in all_infected):
                continue

            if(id1 in all_infected or id2 in all_infected):

                outName = id1+'_' +id2  + '.csv'
                g_rows = len(all_id[i])
                s_rows = len(all_id[j])       

                x_start = ''
                x_lat = 0
                x_long = 0
                for x in range(g_rows):       
                    g_start = all_id[i][x][3]
                    g_end = all_id[i][x][4]
                    for y in range(s_rows):
                        s_start = all_id[j][y][3]
                        s_end = all_id[j][y][4]

                        if((s_end < g_start) or (g_end < s_start)):
                            continue

                        s_confidence = all_id[j][y][5]
                        g_confidence = all_id[i][x][5]

                        if(s_confidence == -1 and g_confidence !=-1 and  g_confidence < neg_confi):
                            continue
                        if(g_confidence == -1 and s_confidence !=-1 and  s_confidence < neg_confi):
                            continue

                        g_lat = all_id[i][x][1]
                        g_long = all_id[i][x][2]
                        s_lat = all_id[j][y][1]
                        s_long = all_id[j][y][2]
                        dx = (s_lat - g_lat)
                        dx = abs(dx)
                        dy = (s_long - g_long)
                        dy = abs(dy)

                        if(dx>r_lat):
                            continue
                        if(dy>r_lng):
                            continue



                        if(s_confidence == -1 or g_confidence == -1 ):
                            net_confi = (s_confidence * g_confidence)
                        else:
                            net_confi = (s_confidence + g_confidence)/2
                        net_confi = net_confi*index_dict[id1]
                        s = max(s_start,g_start)
                        e = min(s_end,g_end)  
                        if(s>e):
                            continue
                        temp = []
                        temp.append(id1)
                        temp.append(id2)
                        temp.append((s_lat + g_lat)/2)
                        temp.append((s_long + g_long)/2)
                        t_s = s/1000
                        t_e = e/1000
                        s = datetime.datetime.fromtimestamp(s / 1e3)
                        e = datetime.datetime.fromtimestamp(e / 1e3)
                        s = str(s)
                        if(s!=x_start ):
                            count = count + 1
                            durat = durat + (t_e - t_s)
                            x_start = s
                            temp.append(str(s))
                            temp.append(str(e))
                            temp.append(g_confidence)
                            temp.append(s_confidence)
                            temp.append(net_confi)
                            scr = scr + abs(net_confi)
                            output.append(temp)
                            combined.append(temp)
                            x_temp = temp
                            x_start = s
                            x_end = e
                            new_infected.append(j)
    #             use these next 3 lines if u want pair wise csv as well
    #                     with open(outName, "w", newline="") as f:
    #                         writer = csv.writer(f)
    #                         writer.writerows(output)
                infected_score[id2] = scr
                num_intersect[id2] = count
                dur_intersect[id2] = durat
                
    #         print(id2,scr)
        return new_infected

            
    extract()
    # print("--- %s seconds till extraction ---" % (time.time() - start_time))

    def infection_spread(depth,all_infected,all_file_names):
        if(depth>levels):
            return
        for x in all_infected:
            temp = x + '.json'
            new_infected=[]
            new_infected = intersect(all_file_names.index(temp))
            new_infected = set(new_infected)
            new_infected = list(new_infected)

            if(len(new_infected)==0):
    #             print('bazinga')
                continue
            print(new_infected)
            
            for i in new_infected:
                temp = all_file_names[i]
                temp = temp.split('.')
                temp = str(temp[0])
                score = infected_score[temp]
                level_intersect[temp] = (depth)+1
                score = score/100
                down = (2**(-1*(depth)))
                up = down*2 *0.999
                inf = down*score
                inf = min(inf,up)

                index_dict[temp] = inf
                all_infected.append(temp)
            all_infected = list(set(all_infected))
        return infection_spread(depth+1,all_infected,all_file_names)

    infection_spread(1,all_infected,all_file_names)
    # print(index_dict)
    # with open('all_intersect.csv', "w", newline="") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(combined)
        
    with open('scores.csv', 'w') as f:
        f.write("'ID','Confidence Score','# Intersections','Duration(in sec)','Level of Transmission'\n")
        for key in index_dict.keys():
            f.write("%s,%s,%s,%s,%s\n"%(key,index_dict[key],num_intersect[key],dur_intersect[key],level_intersect[key])) 
            
    # print("--- %s seconds till completion ---" % (time.time() - start_time))
