#!python3
# -*- coding: cp1251 -*-

"""
#----------------------------------------------------------------------
# Description: Grand-Smeta (server) licenses keys reseter
# Author:  Artyom Breus <Artyom.Breus@gmail.com>
# Created at: Fri Apr 17 17:02:07 VLAT 2020
# Computer: VOSTOK-WS777 #
# Copyright (c) 2020 Artyom Breus  All rights reserved.
#
#----------------------------------------------------------------------

*  This program is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 3 of the License, or
*  (at your option) any later version.
*
*  This program is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import urllib3                       
from configparser import ConfigParser
import os
from pprint import pprint



MASK_LIST 	= ['MSK','KHAB']
USE_XMASK	= False
XMASK_LIST	= ['VLAD','CHITA']
LIC_SERVER 	= "http://10.0.198.38:3185"
POOL		= [0,20]
PASSWORD	= "admin"




def read_config():	
	global MASK_LIST, USE_XMASK, XMASK_LIST, LIC_SERVER, POOL

	config = ConfigParser()
	path = os.path.dirname(os.path.abspath(__file__))

	config.read(path + '\\settings.ini')

	LIC_SERVER 	= config.get('DEFAULT','Server')
	MASK_LIST 	= config.get('DEFAULT','Masks').split(",")
	if MASK_LIST == [] or MASK_LIST == ['*']:
		MASK_LIST = ['',]
	USE_XMASK	= config.getboolean('DEFAULT','UseExclusionMasks')
	XMASK_LIST	= config.get('DEFAULT','ExclusionMasks').split(",")
	POOL		= [int(x) for x in config.get('DEFAULT','LicensesPool').split(",")]
	POOL 		= [POOL[0], POOL[1]+1]
	#pprint(globals())
	
def drop_license(http, cookies, lic_num):
	http.request('GET', r'%(LIC_SERVER)s/objparams.htm?drop_lic_id=%(num)s'%{'LIC_SERVER':LIC_SERVER,'num':lic_num}, headers = { 'Cookie' : cookies } )
	#print("DROP")
	return


def process_licenses():
	http = urllib3.PoolManager()
	request = http.request('GET', '%(LIC_SERVER)s/set_properties.htm?pas=%(PASSWORD)s'%globals())
	cookies = request.headers['Set-Cookie']
	for lic_num in range(*POOL):
		request = http.request('GET', '%(LIC_SERVER)s/objparams.htm?lic_id=%(num)s'%{'LIC_SERVER':LIC_SERVER,'num':lic_num}, headers = { 'Cookie' : cookies } )
		data 	= request.data.decode('utf-8','ignore')		
		if '404 Not Found' in data:
			print("Лицензия № {} не существует - измените размер пула (LicensesPool)".format(lic_num))
			continue
		try:
			idx 	= data.index('Хост:')
		except ValueError:
			print("Лицензия № {} занята неизвестным хостом \n {}".format(lic_num,data))
			continue 		
		idx2	= data[idx+6:].index('<')
		user_pc = data[idx+6:idx+6+idx2]
		if not 'drop_lic_id' in data:
			print("Лицензия № {} \tзанята хостом\t {}".format(lic_num,user_pc))
			continue
		# Отбирать лицензии у всех у кого название хоста не соотвествует XMASK	
		if USE_XMASK:
			if not set([(lambda user_pc,mask: user_pc.startswith(mask))(user_pc,mask) for mask in XMASK_LIST]).pop():
				drop_license(http, cookies, lic_num)	
				print("Лицензия № {} \tвысвобождена у хоста\t {}".format(lic_num,user_pc))
				continue
		# Если хост подходит под маску то отбираем у него лицензию			
		if True in [(lambda user_pc,mask: user_pc.startswith(mask))(user_pc,mask) for mask in MASK_LIST]:
			drop_license(http, cookies, lic_num)
			print("Лицензия № {} \tвысвобождена у хоста\t {} ".format(lic_num,user_pc))
	return	


def main():
	read_config()
	process_licenses()
	
if __name__ == '__main__':
	main()