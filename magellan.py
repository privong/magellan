# magellan library

import math

def GreatCircDist(loc1,loc2):
  dlat=loc2[0]-loc1[0]
  dlong=loc2[1]-loc2[1]
  rdlat=math.radians(dlat)
  rdlong=math.radians(dlong)
  ha=math.sin(rdlat/2) * math.sin(rdlat/2) + math.cos(math.radians(loc1[1])) * math.cos(math.radians(loc1[1]))*math.sin(rdlong/2) * math.sin(rdlong/2)
  hc= 2 * math.atan2(math.sqrt(ha), math.sqrt(1-ha))
  return 6378.1*hc
