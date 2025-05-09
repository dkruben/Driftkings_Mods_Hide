package driftkings.views.battle
{
	import flash.events.Event;
    import flash.filters.DropShadowFilter;
    import flash.geom.ColorTransform;
    import flash.text.AntiAliasType;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import net.wg.gui.battle.components.BattleAtlasSprite;
	import net.wg.gui.battle.random.views.BattlePage;
	import scaleform.gfx.TextFieldEx;
	import driftkings.views.battle.utils.Utils;
	import mods.common.BattleDisplayable;

	public class DriftkingsPlayersPanelAPI extends BattleDisplayable
	{
		public var flashLogS:Function;

		private var configs:Object = {};
		private var textFields:Object = {};

		public function DriftkingsPlayersPanelAPI()
		{
			super();
			name = this.componentName;
		}

		public function as_create(linkage:String, config:Object) : void
		{
			this.createComponent(linkage, config);
		}

		public function as_update(linkage:String, data:Object) : void
		{
			this.updateComponent(linkage, data);
		}

		public function as_hasOwnProperty(linkage:String) : Boolean
		{
			return this.hasOwnPropertyComponent(linkage);
		}

		public function as_delete(linkage:String) : void
		{
			this.deleteComponent(linkage);
		}

		private function hasOwnPropertyComponent(linkage:String) : Boolean
		{
			return this.configs.hasOwnProperty(linkage);
		}

		private function createComponent(linkage:String, config:Object) : void
		{
			this.configs[linkage] = config;
			this.textFields[linkage] = {};
		}

		public function deleteComponent(linkage:String) : void
		{
			if (this.textFields[linkage])
			{
				for (var vehicleID:String in this.textFields[linkage])
				{
					if (this.textFields[linkage][vehicleID] is TextField)
					{
						var textField:TextField = this.textFields[linkage][vehicleID];
						if (textField.parent)
						{
							textField.parent.removeChild(textField);
						}
					}
				}
			}
			delete this.configs[linkage];
			delete this.textFields[linkage];
		}

		private function getListItem(list:*, vehicleID:Number) : *
		{
			if (!list || !list._items)
			{
				return null;
			}
			var itemCount:int = int(list._items.length);
			for (var i:int = 0; i < itemCount; i++)
			{
				if (list._items[i] && list._items[i].vehicleID == vehicleID)
				{
					return list._items[i]._listItem;
				}
			}
			return null;
		}

		public function as_getPPListItem(vehicleID:int) : *
		{
			if (!this.battlePage)
			{
				return null;
			}
			var listRight:* = (this.battlePage as BattlePage).playersPanel.listRight;
			if (!listRight || !listRight.getHolderByVehicleID(int(vehicleID)))
			{
				var listLeft:* = (this.battlePage as BattlePage).playersPanel.listLeft;
				return this.getListItem(listLeft, vehicleID);
			}
			return this.getListItem(listRight, vehicleID);
		}

		private function isRightP(vehicleID:int) : Boolean
		{
			if (!this.battlePage)
			{
				return false;
			}
			var listRight:* = (this.battlePage as BattlePage).playersPanel.listRight;
			return listRight && listRight.getHolderByVehicleID(int(vehicleID));
		}

		public function as_updatePosition(linkage:String, vehicleID:int) : void
		{
			var listItem:* = undefined;
			var config:Object = null;
			var isRight:Boolean = this.isRightP(vehicleID);
			if (!this.textFields[linkage] || !this.configs[linkage])
			{
				return;
			}
			if(!this.textFields[linkage].hasOwnProperty(int(vehicleID)))
			{
				this.createPpanelTF(linkage, int(vehicleID));
			}
			listItem = this.as_getPPListItem(int(vehicleID));
			if (!listItem)
			{
				return;
			}
			config = this.configs[linkage][isRight ? "right" : "left"];
			if (!config || !this.configs[linkage]["holder"])
			{
				return;
			}
			this.textFields[linkage][vehicleID].x = listItem[this.configs[linkage]["holder"]].x + config.x;
			this.textFields[linkage][vehicleID].y = listItem[this.configs[linkage]["holder"]].y + config.y;
		}

		public function as_shadowListItem(show:Object) : *
		{
			if (!show)
			{
				return null;
			}
			return Utils.getDropShadowFilter(show.distance || 0, show.angle || 45, show.color || "#FFFFFF", show.alpha || 1, show.blurX || 2, show.blurY || 2, show.strength || 1);
		}

		public function extendedSetting(linkage:String, vehicleID:int) : *
		{
			if (!this.textFields[linkage])
			{
				return null;
			}
			if(!this.textFields[linkage].hasOwnProperty(int(vehicleID)))
			{
				this.createPpanelTF(linkage, int(vehicleID));
			}
			return this.textFields[linkage][vehicleID];
		}

		public function as_vehicleIconColor(vehicleID:int, colorValue:String) : void
		{
			var listItem:* = undefined;
			var vehicleIcon:BattleAtlasSprite = null;
			listItem = this.as_getPPListItem(int(vehicleID));
			if (listItem && listItem.vehicleIcon)
			{
				vehicleIcon = listItem.vehicleIcon;
				vehicleIcon["DriftkingsPlayersPanelAPI"] = {"color":Utils.colorConvert(colorValue)};
				if(!vehicleIcon.hasEventListener(Event.RENDER))
				{
					vehicleIcon.addEventListener(Event.RENDER, this.onRenderHandle);
				}
			}
		}

		private function onRenderHandle(event:Event) : void
		{
			var sprite:BattleAtlasSprite = event.target as BattleAtlasSprite;
			if (!sprite || !sprite["DriftkingsPlayersPanelAPI"] || !sprite["DriftkingsPlayersPanelAPI"]["color"])
			{
				return;
			}
			var colorTransform:ColorTransform = sprite.transform.colorTransform;
			colorTransform.color = sprite["DriftkingsPlayersPanelAPI"]["color"];
			sprite.transform.colorTransform = colorTransform;
		}

		private function updateComponent(linkage:String, data:Object) : void
		{
			if (!data || !data.hasOwnProperty("vehicleID") || !data.hasOwnProperty("text"))
			{
				return;
			}
			if (!this.textFields[linkage])
			{
				return;
			}
			if(!this.textFields[linkage].hasOwnProperty(int(data.vehicleID)))
			{
				this.createPpanelTF(linkage, int(data.vehicleID));
			}
			if (this.textFields[linkage][data.vehicleID])
			{
				this.textFields[linkage][data.vehicleID].htmlText = data.text;
			}
		}

		private function createPpanelTF(linkage:String, vehicleID:int) : void
		{
			var childIndex:Number = 0;
			var listItem:* = undefined;
			var config:Object = null;
			var shadow:Object = null;
			var isRight:Boolean = this.isRightP(vehicleID);
			var textField:TextField = null;
			var filter:DropShadowFilter = null;
			if (!this.configs[linkage])
			{
				return;
			}
			listItem = this.as_getPPListItem(int(vehicleID));
			if (!listItem)
			{
				return;
			}
			config = this.configs[linkage][isRight ? "right" : "left"];
			if (!config)
			{
				return;
			}
			shadow = this.configs[linkage]["shadow"] || {};
			textField = new TextField();
			TextFieldEx.setNoTranslate(textField, true);
			if (this.configs[linkage]["child"] && listItem[this.configs[linkage]["child"]])
			{
				childIndex = Number(listItem.getChildIndex(listItem[this.configs[linkage]["child"]]));
				listItem.addChildAt(textField, childIndex + 1);
			}
			else
			{
				listItem.addChild(textField);
			}
			textField.defaultTextFormat = new TextFormat("$UniversCondC", 16, Utils.colorConvert("#ffffff"), false, false, false, "", "", "left", 0, 0, 0, 0);
			textField.mouseEnabled = false;
			textField.background = false;
			textField.backgroundColor = 0;
			textField.embedFonts = true;
			textField.multiline = true;
			textField.selectable = false;
			textField.tabEnabled = false;
			textField.antiAliasType = AntiAliasType.ADVANCED;
			textField.width = config.width || 100;
			textField.height = config.height || 20;
			textField.autoSize = config.align || "left";
			filter = Utils.getDropShadowFilter(shadow.distance || 0,  shadow.angle || 45, shadow.color || "#FFFFFF", shadow.alpha || 1, shadow.blurX || 2, shadow.blurY || 2, shadow.strength || 1);
			textField.filters = [filter];
			if (this.configs[linkage]["holder"] && listItem[this.configs[linkage]["holder"]])
			{
				textField.x = listItem[this.configs[linkage]["holder"]].x + (config.x || 0);
				textField.y = listItem[this.configs[linkage]["holder"]].y + (config.y || 0);
			}
			this.textFields[linkage][vehicleID] = textField;
		}
	}
}