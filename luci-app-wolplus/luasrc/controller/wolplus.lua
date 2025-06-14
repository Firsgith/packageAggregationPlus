module("luci.controller.wolplus", package.seeall)
local t, a
local x = luci.model.uci.cursor()
local sys = require "luci.sys" 

function index()
    if not nixio.fs.access("/etc/config/wolplus") then return end
    entry({"admin", "services", "wolplus"}, cbi("wolplus"), _("Wake on LAN"), 95).dependent = true
	entry( {"admin", "services", "wolplus", "awake"}, post("awake") ).leaf = true
	entry( {"admin", "services", "wolplus", "get_name"}, call("get_name") ).leaf = true
end

function get_name(sections)
	local e = {}
	e["name"] = x:get("wolplus", sections, "name")
	luci.http.prepare_content("application/json")
	luci.http.write_json(e)
end

function awake(sections)
	lan = x:get("wolplus",sections,"maceth")
	mac = x:get("wolplus",sections,"macaddr")
	name = x:get("wolplus",sections,"name") or "未知设备"

	-- Extract the raw MAC address for the etherwake command
	local raw_mac = mac:match("([^%s]+)")

    local e = {}
    cmd = "/usr/bin/etherwake -D -i " .. lan .. " -b " .. raw_mac .. " 2>&1"
	local p = io.popen(cmd)
	local msg = ""
	if p then
		while true do
			local l = p:read("*l")
			if l then
				if #l > 100 then l = l:sub(1, 100) .. "..." end
				msg = msg .. l
			else
				break
			end
		end
		p:close()
	end
	e["data"] = msg
	e["name"] = name
	e["macaddr_formatted"] = raw_mac
	
	
	local mac_hint = ""
	sys.net.mac_hints(function(mac, hint_name)
		if mac == raw_mac then
			mac_hint = hint_name
		end
	end)
	e["mac_hint"] = mac_hint
	
    luci.http.prepare_content("application/json")
    luci.http.write_json(e)
end