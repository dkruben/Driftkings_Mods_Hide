package
{
	import flash.events.Event;
	import flash.filters.DropShadowFilter;
	import flash.text.TextField;
	import flash.utils.Dictionary;
	// WG IMPORT
	import net.wg.gui.lobby.techtree.nodes.NationTreeNode;
   
	public dynamic class NationTreeNodeSkinned extends NationTreeNode
	{
		public var __setPropDict:Dictionary = new Dictionary(true);
		public var __lastFrameProp:int = -1;
      
		private var _markTF:TextField = null;
		private var _markPosX:int = 0;
		private var _markPosY:int = 0;
		private var _markHeight:int = 0;
		private var _markWidth:int = 0;
		private var _cachedText:String = "";
		private var __uiF376:int = 0;
      
		public function NationTreeNodeSkinned()
		{
			addFrameScript(0,this.frame1,8,this.frame9,16,this.frame17,24,this.frame25,32,this.frame33,40,this.frame41,48,this.frame49,56,this.frame57,64,this.frame65,72,this.frame73,80,this.frame81,88,this.frame89,96,this.frame97,104,this.frame105,112,this.frame113,120,this.frame121,128,this.frame129,136,this.frame137,144,this.frame145,152,this.frame153,160,this.frame161,168,this.frame169,176,this.frame177,184,this.frame185,192,this.frame193,200,this.frame201,208,this.frame209,216,this.frame217,224,this.frame225,232,this.frame233,240,this.frame241,248,this.frame249,256,this.frame257,264,this.frame265,272,this.frame273,280,this.frame281,288,this.frame289,296,this.frame297,304,this.frame305,312,this.frame313,320,this.frame321,328,this.frame329,336,this.frame337,344,this.frame345,352,this.frame353,360,this.frame361,368,this.frame369,376,this.frame377,384,this.frame385,392,this.frame393,400,this.frame401,408,this.frame409,416,this.frame417,424,this.frame425,432,this.frame433,440,this.frame441,448,this.frame449,456,this.frame457,464,this.frame465,472,this.frame473,480,this.frame481);
			super();
			try
			{
				this.__setProp_typeAndLevel_NationTreeNodeSkinned_typeandlevel_0();
			}
			catch(e:Error)
			{}
			addEventListener(Event.FRAME_CONSTRUCTED, this.__setProp_handler, false, 0, true);
		}
      
		internal function __setProp_typeAndLevel_NationTreeNodeSkinned_typeandlevel_0() : *
		{
			try
			{
				typeAndLevel["componentInspectorSetting"] = true;
			}
			catch(e:Error)
			{
			}
			try {
				typeAndLevel.UIID = 19529730;
				typeAndLevel.enabled = true;
				typeAndLevel.enableInitCallback = false;
				typeAndLevel.visible = true;
			}
			catch(e:Error)
			{}
			try
			{
				typeAndLevel["componentInspectorSetting"] = false;
			}
			catch(e:Error)
			{}
		}
      
		override protected function validateData() : void
		{
			try
			{
				super.validateData();
			}
			catch (e:Error)
			{}
			try {
				if (this.nameTF != null)
				{
					var nodeText:String = String(this.nameTF.text || "");
					var position:Array = nodeText.split("||");
					if (position && position.length > 0)
					{
						var _text:String = String(position[0] || "");
						if (position.length > 1)
						{
							var place:String = String(position[1] || "");
							this._cachedText = place;
							if (position.length >= 6)
							{
								var posX:Number = Number(position[2]);
								var posY:Number = Number(position[3]);
								var height:Number = Number(position[4]);
								var width:Number = Number(position[5]);
								this._markPosX = !isNaN(posX) ? int(posX) : 0;
								this._markPosY = !isNaN(posY) ? int(posY) : 0;
								this._markHeight = !isNaN(height) ? int(height) : 20;
								this._markWidth = !isNaN(width) ? int(width) : 100;
								if (!this._markTF)
								{
									this._markTF = new TextField();
									this._markTF.antiAliasType = "advanced";
									this._markTF.multiline = true;
									this._markTF.selectable = false;
									this._markTF.filters = [new DropShadowFilter(0, 90, 0, 0.72, 3, 3, 2, 2)];
									this.addChild(this._markTF);
								}
								this._markTF.x = this._markPosX;
								this._markTF.y = this._markPosY;
								this._markTF.height = this._markHeight;
								this._markTF.width = this._markWidth;
								this._markTF.htmlText = place;
							}
						}
                  
						if (this.nameTF)
						{
							this.nameTF.text = _text;
						}
					}
				}
			}
			catch (e:Error)
			{}
		}
      
		override protected function draw() : void
		{
			try
			{
				super.draw();
			}
			catch (e:Error)
			{}
			try
			{
				if (this._markTF)
				{
					this._markTF.x = this._markPosX;
					this._markTF.y = this._markPosY;
					this._markTF.height = Math.max(1, this._markHeight);
					this._markTF.width = Math.max(1, this._markWidth);
					this._markTF.htmlText = this._cachedText || "";
				}
			}
			catch (e:Error)
			{}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_0(param1:int) : *
		{
			var frame:int = param1;
			if (!(button != null && frame >= 1 && frame <= 81 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 1 && int(this.__setPropDict[button]) <= 81))))
			{
				return;
			}
			this.__setPropDict[button] = frame;
			try
			{
				button["componentInspectorSetting"] = true;
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "center";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {"subString": "{xp_cost}", "source": "button_xp_cost_icon", "baseLineY": 13, "width": 16, "height": 16};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				button["componentInspectorSetting"] = false;
			}
			catch (e:Error)
			{}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_81(param1:int) : *
		{
			var frame:int = param1;
			if (!(button != null && frame >= 82 && frame <= 161 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 82 && int(this.__setPropDict[button]) <= 161))))
			{
				return;
			}
			this.__setPropDict[button] = frame;
			try
			{
				button["componentInspectorSetting"] = true;
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "center";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {"subString": "{credits}", "source": "button_credits_icon", "baseLineY": 13, "width": 16, "height": 16};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				button["componentInspectorSetting"] = false;
			}
			catch (e:Error)
			{}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_161(param1:int) : *
		{
			var frame:int = param1;
			if (!(button != null && frame >= 162 && frame <= 361 &&  (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 162 && int(this.__setPropDict[button]) <= 361))))
			{
				return;
			}
			this.__setPropDict[button] = frame;
			try {
				button["componentInspectorSetting"] = true;
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "center";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {"subString": "{gold}", "source": "button_gold_icon", "baseLineY": 13, "width": 16, "height": 16};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				button["componentInspectorSetting"] = false;
			}
			catch (e:Error)
			{}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_361(param1:int) : *
		{
			var frame:int = param1;
			if (!(button != null && frame >= 362 && frame <= 481 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 362 && int(this.__setPropDict[button]) <= 481))))
			{
				return;
			}
			this.__setPropDict[button] = frame;
			try {
				button["componentInspectorSetting"] = true;
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "none";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {"subString": "{xp_cost}", "source": "button_xp_cost_icon", "baseLineY": 13, "width": 16, "height": 16};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				button["componentInspectorSetting"] = false;
			}
			catch (e:Error)
			{}
		}
      
		internal function __setProp_handler(param1:Object) : *
		{
			try
			{
				var _loc2_:int = int(currentFrame);
				if (this.__lastFrameProp == _loc2_)
				{
					return;
				}
				this.__lastFrameProp = _loc2_;
				this.__setProp_button_NationTreeNodeSkinned_button_0(_loc2_);
				this.__setProp_button_NationTreeNodeSkinned_button_81(_loc2_);
				this.__setProp_button_NationTreeNodeSkinned_button_161(_loc2_);
				this.__setProp_button_NationTreeNodeSkinned_button_361(_loc2_);
			}
			catch (e:Error)
			{}
		}
      
		internal function frame1() : * { stop(); }
		internal function frame9() : * { stop(); }
		internal function frame17() : * { stop(); }
		internal function frame25() : * { stop(); }
		internal function frame33() : * { stop(); }
		internal function frame41() : * { stop(); }
		internal function frame49() : * { stop(); }
		internal function frame57() : * { stop(); }
		internal function frame65() : * { stop(); }
		internal function frame73() : * { stop(); }
		internal function frame81() : * { stop(); }
		internal function frame89() : * { stop(); }
		internal function frame97() : * { stop(); }
		internal function frame105() : * { stop(); }
		internal function frame113() : * { stop(); }
		internal function frame121() : * { stop(); }
		internal function frame129() : * { stop(); }
		internal function frame137() : * { stop(); }
		internal function frame145() : * { stop(); }
		internal function frame153() : * { stop(); }
		internal function frame161() : * { stop(); }
		internal function frame169() : * { stop(); }
		internal function frame177() : * { stop(); }
		internal function frame185() : * { stop(); }
		internal function frame193() : * { stop(); }
		internal function frame201() : * { stop(); }
		internal function frame209() : * { stop(); }
		internal function frame217() : * { stop(); }
		internal function frame225() : * { stop(); }
		internal function frame233() : * { stop(); }
		internal function frame241() : * { stop(); }
		internal function frame249() : * { stop(); }
		internal function frame257() : * { stop(); }
		internal function frame265() : * { stop(); }
		internal function frame273() : * { stop(); }
		internal function frame281() : * { stop(); }
		internal function frame289() : * { stop(); }
		internal function frame297() : * { stop(); }
		internal function frame305() : * { stop(); }
		internal function frame313() : * { stop(); }
		internal function frame321() : * { stop(); }
		internal function frame329() : * { stop(); }
		internal function frame337() : * { stop(); }
		internal function frame345() : * { stop(); }
		internal function frame353() : * { stop(); }
		internal function frame361() : * { stop(); }
		internal function frame369() : * { stop(); }
		internal function frame377() : * { stop(); }
		internal function frame385() : * { stop(); }
		internal function frame393() : * { stop(); }
		internal function frame401() : * { stop(); }
		internal function frame409() : * { stop(); }
		internal function frame417() : * { stop(); }
		internal function frame425() : * { stop(); }
		internal function frame433() : * { stop(); }
		internal function frame441() : * { stop(); }
		internal function frame449() : * { stop(); }
		internal function frame457() : * { stop(); }
		internal function frame465() : * { stop(); }
		internal function frame473() : * { stop(); }
		internal function frame481() : * { stop(); }
	}
}