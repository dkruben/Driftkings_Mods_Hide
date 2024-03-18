# -*- coding: utf-8 -*-
import math
from collections import OrderedDict

from CurrentVehicle import g_currentVehicle
from goodies.goodie_constants import GOODIE_STATE
from gui.Scaleform.daapi.view.battle.shared.consumables_panel import ConsumablesPanel
from gui.Scaleform.daapi.view.lobby.storage import storage_helpers
from gui.impl import backport
from gui.impl.gen import R
from gui.shared.formatters import icons
from gui.shared.formatters import text_styles
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.items_parameters import formatters, functions
from gui.shared.items_parameters import params
from gui.shared.tooltips import formatters as formatters_tooltips
from gui.shared.tooltips import module
from gui.shared.tooltips.common import _CurrencySetting
from gui.shared.tooltips.module import CommonStatsBlockConstructor as CommonStatsBlockConstructor1
from gui.shared.tooltips.module import StatusBlockConstructor
from gui.shared.tooltips.shell import CommonStatsBlockConstructor
from gui.shared.utils.requesters import REQ_CRITERIA
from helpers.i18n import makeString as makeString

from DriftkingsCore import SimpleConfigInterface, Analytics, override, registerEvent


class ConfigInterface(SimpleConfigInterface):

    def __init__(self):
        self.colors = OrderedDict({
            ('ColorPositive', '#28F09C'),
            ('ColorNeutral', '#7CD606'),
            ('Stabilization', '#FFD700'),
            ('MovementSpeed', '#8378FC'),
            ('RotatingVehicle', '#1CC6D9'),
            ('RotatingTurret', '#F200DA'),
            ('ModulesColor', '#FFA500')
        })
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.2.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_StabBonus_text': 'Stabilization bonus',
            'UI_setting_StabBonus_tooltip': '',
            'UI_setting_Stabilization_text': 'Total stabilization',
            'UI_setting_Stabilization_tooltip': '',
            'UI_setting_MovementSpeed_text': 'When maximum speed',
            'UI_setting_MovementSpeed_tooltip': '',
            'UI_setting_RotatingVehicle_text': 'When turning vehicle',
            'UI_setting_RotatingVehicle_tooltip': '',
            'UI_setting_RotatingTurret_text': 'When turning turret',
            'UI_setting_RotatingTurret_tooltip': '',
            'UI_setting_modulesText_text': '[To modules] <font color=\'' + self.colors['ModulesColor'] + '\'>>{}</font>',
            'UI_setting_modulesText_tooltip': '',
            'UI_setting_modulesTextTooltip_text': ' [To modules]',
            'UI_setting_modulesTextTooltip_tooltip': '',
            'UI_setting_modulesTextTooltipBattle_text': '%s, <font color=\'' + self.colors['ModulesColor'] + '\'>[To modules] %s</font>',
            'UI_setting_modulesTextTooltipBattle_tooltip': '',
            'UI_setting_tracerSpeedText_text': '[Tracer]',
            'UI_setting_tracerSpeedText_tooltip': '',
            'UI_setting_shellSpeedText_text': '[Shell]',
            'UI_setting_shellSpeedText_tooltip': '',
            'UI_setting_speedMsec_text': 'm/sec.',
            'UI_setting_speedMsec_tooltip': ''
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [],
            'column2': []}

    @staticmethod
    def getAdditiveShotDispersionFactor(vehicle):
        additiveShotDispersionFactor = vehicle.descriptor.miscAttrs['additiveShotDispersionFactor']
        for crewman in vehicle.crew:
            if crewman[1] is None:
                continue
            if 'gunner_smoothTurret' in crewman[1].skillsMap:
                additiveShotDispersionFactor -= crewman[1].skillsMap['gunner_smoothTurret'].level * 0.00075
            if 'driver_smoothDriving' in crewman[1].skillsMap:
                additiveShotDispersionFactor -= crewman[1].skillsMap['driver_smoothDriving'].level * 0.0004
        for item in vehicle.battleBoosters.installed.getItems():
            if item and 'imingStabilizer' in item.name:
                additiveShotDispersionFactor -= 0.05
        for item in vehicle.optDevices.installed.getItems():
            if item and 'imingStabilizer' in item.name:
                if 'pgraded' in item.name:
                    additiveShotDispersionFactor -= 0.25
                elif 'mproved' in item.name:
                    additiveShotDispersionFactor -= 0.275
                else:
                    additiveShotDispersionFactor -= 0.2
        return additiveShotDispersionFactor

    def getStabFactors(self, vehicle, module, inSettings=False):
        typeDescriptor = vehicle.descriptor
        factors = functions.getVehicleFactors(vehicle)
        additiveFactor = self.getAdditiveShotDispersionFactor(vehicle)
        chassisShotDispersionFactorsMovement, chassisShotDispersionFactorsRotation = typeDescriptor.chassis.shotDispersionFactors
        gunShotDispersionFactorsTurretRotation = module.descriptor.shotDispersionFactors['turretRotation']
        chassisShotDispersionFactorsMovement /= factors['vehicle/rotationSpeed']
        gunShotDispersionFactorsTurretRotation /= factors['turret/rotationSpeed']
        vehicleRSpeed = turretRotationSpeed = 0
        maxTurretRotationSpeed = typeDescriptor.turret.rotationSpeed
        vehicleRSpeedMax = typeDescriptor.physics['rotationSpeedLimit']
        vehicleSpeed = typeDescriptor.siegeVehicleDescr.physics['speedLimits'][0] if typeDescriptor.isWheeledVehicle and hasattr(typeDescriptor, 'siegeVehicleDescr') else typeDescriptor.physics['speedLimits'][0]
        vehicleSpeed *= 3.6
        vehicleSpeedMax = 99.0 if typeDescriptor.isWheeledVehicle and hasattr(typeDescriptor, 'siegeVehicleDescr') else 70.0

        vehicleMovementFactor = vehicleSpeed * chassisShotDispersionFactorsMovement
        vehicleMovementFactor *= vehicleMovementFactor
        vehicleMovementFactorMax = vehicleSpeedMax * chassisShotDispersionFactorsMovement
        vehicleMovementFactorMax *= vehicleMovementFactorMax

        vehicleRotationFactorMax = vehicleRSpeedMax * chassisShotDispersionFactorsRotation
        vehicleRotationFactorMax *= vehicleRotationFactorMax
        vehicleRotationFactor = vehicleRSpeed * chassisShotDispersionFactorsRotation
        vehicleRotationFactor *= vehicleRotationFactor

        turretRotationFactorMax = maxTurretRotationSpeed * gunShotDispersionFactorsTurretRotation
        turretRotationFactorMax *= turretRotationFactorMax
        turretRotationFactor = turretRotationSpeed * gunShotDispersionFactorsTurretRotation
        turretRotationFactor *= turretRotationFactor

        idealFactorMax = vehicleMovementFactorMax + vehicleRotationFactorMax + turretRotationFactorMax

        baseMax = round(math.sqrt(idealFactorMax), 1)
        baseMovementSpeed = round(math.sqrt(vehicleMovementFactor), 2)
        baseRotatingVehicle = round(math.sqrt(vehicleRotationFactorMax), 2)
        baseRotatingTurret = round(math.sqrt(turretRotationFactorMax), 2)

        resultMax = round(math.sqrt(idealFactorMax * (additiveFactor ** 2)), 1)
        resultMovementSpeed = round(math.sqrt(vehicleMovementFactor * (additiveFactor ** 2)), 2)
        resultRotatingVehicle = round(math.sqrt(vehicleRotationFactorMax * (additiveFactor ** 2)), 2)
        resultRotatingTurret = round(math.sqrt(turretRotationFactorMax * (additiveFactor ** 2)), 2)
        bonuses = (self.i18n['UI_setting_StabBonus_text'], '<font color=\'%s\'>+%.2f%%</font>' % (self.colors['ColorPositive'] if additiveFactor < 1 else self.colors['ColorNeutral'], 100 - additiveFactor / 0.01))
        if baseMax - resultMax > 0:
            bonuses1 = ('%s %.2f%% (<font color=\'%s\'>+%.2f%%</font>)' % (self.i18n['UI_setting_Stabilization_text'], 100 - baseMax, self.colors['ColorPositive'], baseMax - resultMax), '<font color=\'%s\'>%.2f%%</font>' % (self.colors['Stabilization'], 100 - resultMax))
            bonuses2 = ('%s %.2f%% (<font color=\'%s\'>+%.2f%%</font>)' % (self.i18n['UI_setting_MovementSpeed_text'], resultMovementSpeed, self.colors['ColorPositive'], baseMovementSpeed - resultMovementSpeed), '<font color=\'%s\'>%.2f%%</font>' % (self.colors['MovementSpeed'], baseMovementSpeed))
            bonuses3 = ('%s %.2f%% (<font color=\'%s\'>+%.2f%%</font>)' % (self.i18n['UI_setting_RotatingVehicle_text'], resultRotatingVehicle, self.colors['ColorPositive'], baseRotatingVehicle - resultRotatingVehicle), '<font color=\'%s\'>%.2f%%</font>' % (self.colors['RotatingVehicle'], baseRotatingVehicle))
            bonuses4 = ('%s %.2f%% (<font color=\'%s\'>+%.2f%%</font>)' % (self.i18n['UI_setting_RotatingTurret_text'], resultRotatingTurret, self.colors['ColorPositive'], baseRotatingTurret - resultRotatingTurret), '<font color=\'%s\'>%.2f%%</font>' % (self.colors['RotatingTurret'], baseRotatingTurret))
        else:
            bonuses1 = (self.i18n['UI_setting_Stabilization_text'], '<font color=\'%s\'>%.2f%%</font>' % (self.colors['Stabilization'], 100 - resultMax))
            bonuses2 = (self.i18n['UI_setting_MovementSpeed_text'], '<font color=\'%s\'>%.2f%%</font>' % (self.colors['MovementSpeed'], resultMovementSpeed))
            bonuses3 = (self.i18n['UI_setting_RotatingVehicle_text'], '<font color=\'%s\'>%.2f%%</font>' % (self.colors['RotatingVehicle'], resultRotatingVehicle))
            bonuses4 = (self.i18n['UI_setting_RotatingTurret_text'], '<font color=\'%s\'>%.2f%%</font>' % (self.colors['RotatingTurret'], resultRotatingTurret))
        if inSettings:
            return resultMax
        if additiveFactor < 1:
            return bonuses1, bonuses4, bonuses3, bonuses2, bonuses
        return bonuses1, bonuses4, bonuses3, bonuses2


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(storage_helpers, 'createStorageDefVO')
def new_createStorageDefVO(func, itemID, title, description, count, price, image, imageAlt, itemType='', nationFlagIcon='', enabled=True, available=True, contextMenuId='', additionalInfo='', actionButtonLabel=None, active=GOODIE_STATE.INACTIVE, upgradable=False, upgradeButtonIcon=None, upgradeButtonTooltip='', extraParams=(), specializations=()):
    result = func(itemID, title, description, count, price, image, imageAlt, itemType, nationFlagIcon, enabled, available, contextMenuId, additionalInfo, actionButtonLabel, active, upgradable, upgradeButtonIcon, upgradeButtonTooltip, extraParams, specializations)
    b = []
    for priced in result['price']['price']:
        b.append((priced[0], priced[1] * result['count']))
    result['price']['price'] = tuple(b)
    return result


@override(ConsumablesPanel, '_ConsumablesPanel__makeShellTooltip')
def new_makeShellTooltip(func, self, descriptor, piercingPower, shotSpeed):
    result = func(self, descriptor, piercingPower, shotSpeed)
    try:
        damage = backport.getNiceNumberFormat(descriptor.damage[0])
        damageModule = config.i18n['UI_setting_modulesTextTooltipBattle_text'] % (damage, backport.getNiceNumberFormat(descriptor.damage[1]))
    except StandardError:
        return result
    return result.replace(damage, damageModule)


@override(formatters, 'getFormattedParamsList')
def new_getFormattedParamsList(func, descriptor, parameters, excludeRelative=False):
    params = func(descriptor, parameters, excludeRelative)
    result = []
    try:
        for param in params:
            if 'caliber' in param:
                result.append(param)
                result.append(('avgDamage', config.i18n['UI_setting_modulesText_text'].format(backport.getNiceNumberFormat(descriptor.damage[1]))))
            else:
                result.append(param)
    except StandardError:
        return params
    return result


@override(CommonStatsBlockConstructor, 'construct')
def new_construct(func, self):
    result = func(self)
    try:
        block = []
        avgDamage = backport.text(R.strings.menu.moduleInfo.params.dyn('avgDamage')())
        for pack in result:
            if 'name' in pack['data'] and avgDamage in pack['data']['name']:
                block.append(pack)
                block.append(self._packParameterBlock(avgDamage, '<font color=\'#FFA500\'>%s</font>' % backport.getNiceNumberFormat(self.shell.descriptor.damage[1]), makeString(formatters.measureUnitsForParameter('avgDamage')) + config.i18n['UI_settings_modulesTextTooltip_text']))
            else:
                block.append(pack)
        vehicle = g_currentVehicle.item
        module = vehicle.gun
        bonuses = config.getStabFactors(vehicle, module)
        for bonus in bonuses:
            block.append(self._packParameterBlock(bonus[0], bonus[1], ''))
    except StandardError:
        return result
    return block


# We create a corrected constructor for displaying a list of tanks in the tooltip
@registerEvent(module.InventoryBlockConstructor, 'construct')
def new_inventoryBlockConstructorConstruct(self):
    block = []
    module = self.module
    inventoryCount = self.configuration.inventoryCount
    vehiclesCount = self.configuration.vehiclesCount
    if self.module.itemTypeID is GUI_ITEM_TYPE.EQUIPMENT and self.module.isBuiltIn:
        return
    else:
        items = self.itemsCache.items
        if inventoryCount:
            count = module.inventoryCount
            if count > 0:
                block.append(self._getInventoryBlock(count, self._inInventoryBlockData, self._inventoryPadding))
        if vehiclesCount:
            inventoryVehicles = items.getVehicles(REQ_CRITERIA.INVENTORY)
            installedVehicles = module.getInstalledVehicles(inventoryVehicles.itervalues())
            count = len(installedVehicles)
            if count > 0:
                totalInstalledVehicles = [x.shortUserName for x in installedVehicles]
                totalInstalledVehicles.sort()
                tooltipText = None
                visibleVehiclesCount = 0
                for installedVehicle in totalInstalledVehicles:
                    if tooltipText is None:
                        tooltipText = installedVehicle
                        visibleVehiclesCount = 1
                        continue
                    # modified string
                    if len(tooltipText) + len(installedVehicle) + 2 > MAX_INSTALLED_LIST_LEN:
                        break
                    tooltipText = ', '.join((tooltipText, installedVehicle))
                    visibleVehiclesCount += 1

                if count > visibleVehiclesCount:
                    hiddenVehicleCount = count - visibleVehiclesCount
                    hiddenTxt = backport.text(R.strings.tooltips.moduleFits.already_installed.hiddenVehicleCount(), count=str(hiddenVehicleCount))
                    tooltipText = '... '.join((tooltipText, text_styles.stats(hiddenTxt)))
                self._onVehicleBlockData['text'] = tooltipText
                block.append(self._getInventoryBlock(count, self._onVehicleBlockData, self._inventoryPadding))
        return block


@override(StatusBlockConstructor, '_getStatus')
def StatusBlockConstructor_getStatus(func, self):
    self.MAX_INSTALLED_LIST_LEN = 1000
    return func(self)


# adding a display of the sale price of all equipment/consumables in the hangar and on vehicles in the tooltip
@override(module.PriceBlockConstructor, 'construct')
def new_priceBlockConstructorConstruct(func, self):
    # execute the original code
    block = func(self)
    module = self.module
    # we obtain data on the current quantity in the warehouse and on tanks
    inventoryCount = self.configuration.inventoryCount and module.inventoryCount
    vehiclesCount = self.configuration.vehiclesCount and len(module.getInstalledVehicles(self.itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY).itervalues()))
    # checking availability and clarifying that the price is in credits
    if (inventoryCount or vehiclesCount) and module.getBuyPrice().getCurrency() == 'credits' and module.sellPrices.itemPrice.price.credits:
        # type Sale
        settings = _CurrencySetting('#tooltips:vehicle/sell_price', icons.credits(), text_styles.credits, 'credits', iconYOffset=0)
        # We calculate the cost of selling ALL similar equipment/consumables price * (quantity in warehouse + quantity on tanks)
        priceValue = settings.textStyle(backport.getIntegralFormat(module.sellPrices.itemPrice.price.credits * (inventoryCount + vehiclesCount)))
        # add a text hint with quantity
        text = text_styles.concatStylesWithSpace(text_styles.main(settings.text), '(%s + %s)' % (inventoryCount, vehiclesCount))
        # insert the generated result at the end of the cost block
        block.append(formatters_tooltips.packTextParameterWithIconBlockData(name=text, value=priceValue, icon=settings.frame, valueWidth=self._valueWidth, padding=formatters_tooltips.packPadding(left=-5), nameOffset=14, gap=0, iconYOffset=settings.iconYOffset))
    return block


# We add a display of parameters that will change the consumables (first aid kit, cola, etc.) if installed on the tank
@override(module.EffectsBlockConstructor, 'construct')
def new_effectsBlockConstructorConstruct(func, self):
    block = func(self)
    isInstalled = self.module.isInstalled(self.configuration.vehicle)
    if isInstalled:
        kpiArgs = {kpi.name: kpi.value for kpi in self.module.getKpi(self.configuration.vehicle)}
        currParams = params.VehicleParams(self.configuration.vehicle).getParamsDict()
        onUseStr = ''
        sets = {
            'crewLevel': ('reloadTimeSecs', 'clipFireRate', 'autoReloadTime', 'aimingTime', 'shotDispersionAngle', 'avgDamagePerMinute', 'circularVisionRadius'),
            'vehicleEnginePower': ('enginePowerPerTon', 'enginePower', 'turretRotationSpeed'),
            'vehicleFireChance': ('damagedModulesDetectionTimeSituational', 'damagedModulesDetectionTime'),
            'vehicleRepairSpeed': ('chassisRepairTime', 'repairSpeed'),
        }
        for datasheet in sets:
            if datasheet in kpiArgs:
                for param in sets[datasheet]:
                    if param in currParams and currParams[param]:
                        value = currParams[param]
                        if type(value) == int:
                            temp = '%s' % value
                        elif type(value) == float:
                            temp = '%.2f' % value
                        else:
                            temp = '%.2f' % value[0]
                        if 'clipFireRate' in param:
                            temp = '(%.2f/%.2f/%.2f)' % (value[0], value[1], value[2])
                        onUseStr += "<font face='$FieldFont' size='14' color='#80d43a'>%s</font> %s %s\n" % (text_styles.bonusAppliedText(temp), makeString(formatters.measureUnitsForParameter(param)), makeString('#menu:tank_params/%s' % param))
        block.append(formatters_tooltips.packImageTextBlockData(title=text_styles.middleTitle(backport.text(R.strings.tooltips.equipment.always())), desc=text_styles.main(onUseStr), padding=formatters_tooltips.packPadding(top=5)))
    return block


@override(CommonStatsBlockConstructor1, 'construct')
def new_construct1(func, self):
    result = list(func(self))
    try:
        module = self.module
        vehicle = self.configuration.vehicle
        if module.itemTypeID == GUI_ITEM_TYPE.GUN:
            bonuses = config.getStabFactors(vehicle, module)
            for bonus in bonuses:
                result.append(formatters_tooltips.packTextParameterBlockData(name=bonus[0], value=bonus[1], valueWidth=self._valueWidth, padding=formatters_tooltips.packPadding(left=-5)))
    except StandardError:
        pass
    return result


def new_packBlocks(func, self, paramName):
    blocks = func(self, paramName)
    try:
        if paramName in ('relativePower', 'vehicleGunShotDispersion', 'aimingTime'):
            vehicle = g_currentVehicle.item
            module = vehicle.gun
            bonuses = config.getStabFactors(vehicle, module)
            result = []
            found = False
            for block in blocks:
                result.append(block)
                if 'blocksData' in block['data']:
                    if found:
                        continue
                    for linkage in block['data']['blocksData']:
                        if 'TooltipTextBlockUI' in linkage['linkage']:
                            found = True
                            for bonus in bonuses:
                                result.append(formatters_tooltips.packTextParameterBlockData(name='%s:&nbsp;%s' % (bonus[1], bonus[0]), value='', valueWidth=0, padding=formatters_tooltips.packPadding(left=59, right=20)))
                            break
            return result
    except StandardError:
        pass
    return blocks


MAX_INSTALLED_LIST_LEN = 1200
