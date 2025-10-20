package
{
	import flash.events.Event;
	import flash.filters.DropShadowFilter;
	import flash.text.TextField;
	import flash.utils.Dictionary;
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
		private var _masteryTF:TextField = null;
		private var _masteryX:int = 0;
		private var _masteryY:int = 0;
		private var _masteryH:int = 0;
		private var _masteryW:int = 0;
		private var _masteryCachedText:String = "";
      
		public function NationTreeNodeSkinned()
		{
			addFrameScript(0,this.frame1,8,this.frame9,16,this.frame17,24,this.frame25,32,this.frame33,40,this.frame41,48,this.frame49,56,this.frame57,64,this.frame65,72,this.frame73,80,this.frame81,88,this.frame89,96,this.frame97,104,this.frame105,112,this.frame113,120,this.frame121,128,this.frame129,136,this.frame137,144,this.frame145,152,this.frame153,160,this.frame161,168,this.frame169,176,this.frame177,184,this.frame185,192,this.frame193,200,this.frame201,208,this.frame209,216,this.frame217,224,this.frame225,232,this
			.frame233,240,this.frame241,248,this.frame249,256,this.frame257,264,this.frame265,272,this.frame273,280,this.frame281,288,this.frame289,296,this.frame297,304,this.frame305,312,this.frame313,320,this.frame321,328,this.frame329,336,this.frame337,344,this.frame345,352,this.frame353,360,this.frame361,368,this.frame369,376,this.frame377,384,this.frame385,392,this.frame393,400,this.frame401,408,this.frame409,416,this.frame417,424,this.frame425,432,this.frame433,440,this.frame441,448,this.frame449,456,this.frame457
			,464,this.frame465,472,this.frame473,480,this.frame481);
			super();
			this.__setProp_typeAndLevel_NationTreeNodeSkinned_typeandlevel_0();
			addEventListener(Event.FRAME_CONSTRUCTED,this.__setProp_handler,false,0,true);
		}
      
		internal function __setProp_typeAndLevel_NationTreeNodeSkinned_typeandlevel_0() : *
		{
			try
			{
				typeAndLevel["componentInspectorSetting"] = true;
			}
			catch(e:Error)
			{}
			typeAndLevel.UIID = 19529730;
			typeAndLevel.enabled = true;
			typeAndLevel.enableInitCallback = false;
			typeAndLevel.visible = true;
			try
			{
				typeAndLevel["componentInspectorSetting"] = false;
			}
			catch(e:Error)
			{}
		}
      
		override protected function validateData() : void
		{
			super.validateData();
			var _loc1_:String = String(this.nameTF.text);
			var _loc2_:Array = _loc1_.split("||");
			if(_loc2_.length == 6)
			{
				if(!this._markTF)
				{
					this._markTF = new TextField();
					this._markTF.antiAliasType = "advanced";
					this._markTF.multiline = false;
					this._markTF.selectable = false;
					this._markTF.filters = [new DropShadowFilter(0,90,0,0.72,3,3,2,2)];
					this.addChild(this._markTF);
				}
				this._markPosX = int(_loc2_[2]);
				this._markPosY = int(_loc2_[3]);
				this._markHeight = int(_loc2_[4]);
				this._markWidth = int(_loc2_[5]);
				this._cachedText = _loc2_[1];
				this._masteryCachedText = _loc2_[6];
				this._markTF.x = this._markPosX;
				this._markTF.y = this._markPosY;
				this._markTF.height = this._markHeight;
				this._markTF.width = this._markWidth;
				this._markTF.htmlText = this._cachedText;
				this.nameTF.text = _loc2_[0];
				if(!this._masteryTF)
				{
					this._masteryTF = new TextField();
					this._masteryTF.antiAliasType = "advanced";
					this._masteryTF.multiline = true;
					this._masteryTF.selectable = false;
					this._masteryTF.filters = [new DropShadowFilter(0,90,0,0.72,3,3,2,2)];
					this.addChild(this._masteryTF);
				}
				this._masteryX = 0;
				this._masteryY = -26;
				this._masteryH = 26;
				this._masteryW = 128;
			}
			else if(_loc2_.length != 1)
			{
				DebugUtils.LOG_ERROR("validateData: Array length is " + _loc2_.length + " should be 6!");
			}
			else
			{
				this._masteryCachedText = "";
				this._cachedText = "";
			}
		}
      
		override protected function draw() : void
		{
			super.draw();
			if(Boolean(this._markTF))
			{
				this._markTF.x = this._markPosX;
				this._markTF.y = this._markPosY;
				this._markTF.height = this._markHeight;
				this._markTF.width = this._markWidth;
				this._markTF.htmlText = this._cachedText;
			}
			if(Boolean(this._masteryTF))
			{
				this._masteryTF.x = this._masteryX;
				this._masteryTF.y = this._masteryY;
				this._masteryTF.height = this._masteryH;
				this._masteryTF.width = this._masteryW;
				this._masteryTF.htmlText = this._masteryCachedText;
			}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_0(param1:int) : *
		{
			if(button != null && param1 >= 1 && param1 <= 81 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 1 && int(this.__setPropDict[button]) <= 81)))
			{
				this.__setPropDict[button] = param1;
				try
				{
					button["componentInspectorSetting"] = true;
				}
				catch(e:Error)
				{}
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "center";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {
					"subString":"{xp_cost}",
					"source":"button_xp_cost_icon",
					"baseLineY":13,
					"width":16,
					"height":16
				};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				try
				{
					button["componentInspectorSetting"] = false;
				}
				catch(e:Error)
				{}
			}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_81(param1:int) : *
		{
			if(button != null && param1 >= 82 && param1 <= 161 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 82 && int(this.__setPropDict[button]) <= 161)))
			{
				this.__setPropDict[button] = param1;
				try
				{
					button["componentInspectorSetting"] = true;
				}
				catch(e:Error)
				{}
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "center";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {
					"subString":"{credits}",
					"source":"button_credits_icon",
					"baseLineY":13,
					"width":16,
					"height":16
				};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				try
				{
					button["componentInspectorSetting"] = false;
				}
				catch(e:Error)
				{}
			}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_161(param1:int) : *
		{
			if(button != null && param1 >= 162 && param1 <= 361 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 162 && int(this.__setPropDict[button]) <= 361)))
			{
				this.__setPropDict[button] = param1;
				try
				{
					button["componentInspectorSetting"] = true;
				}
				catch(e:Error)
				{}
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "center";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {
					"subString":"{gold}",
					"source":"button_gold_icon",
					"baseLineY":13,
					"width":16,
					"height":16
				};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				try
				{
					button["componentInspectorSetting"] = false;
				}
				catch(e:Error)
				{}
			}
		}
      
		internal function __setProp_button_NationTreeNodeSkinned_button_361(param1:int) : *
		{
			if(button != null && param1 >= 362 && param1 <= 481 && (this.__setPropDict[button] == undefined || !(int(this.__setPropDict[button]) >= 362 && int(this.__setPropDict[button]) <= 481)))
			{
				this.__setPropDict[button] = param1;
				try
				{
					button["componentInspectorSetting"] = true;
				}
				catch(e:Error)
				{}
				button.UIID = 19529729;
				button.autoRepeat = false;
				button.autoSize = "none";
				button.data = "";
				button.enabled = true;
				button.enableInitCallback = false;
				button.focusable = true;
				button.imgSubstitution = {
					"subString":"{xp_cost}",
					"source":"button_xp_cost_icon",
					"baseLineY":13,
					"width":16,
					"height":16
				};
				button.label = "";
				button.selected = false;
				button.soundId = "";
				button.soundType = "normal";
				button.toggle = false;
				try
				{
					button["componentInspectorSetting"] = false;
				}
				catch(e:Error)
				{
				}
			}
		}
      
		internal function __setProp_handler(param1:Object) : *
		{
			var _loc2_:int = int(currentFrame);
			if(this.__lastFrameProp == _loc2_)
			{
				return;
			}
			this.__lastFrameProp = _loc2_;
			this.__setProp_button_NationTreeNodeSkinned_button_0(_loc2_);
			this.__setProp_button_NationTreeNodeSkinned_button_81(_loc2_);
			this.__setProp_button_NationTreeNodeSkinned_button_161(_loc2_);
			this.__setProp_button_NationTreeNodeSkinned_button_361(_loc2_);
		}
      
		internal function frame1() : *
		{
			stop();
		}
      
		internal function frame9() : *
		{
			stop();
		}
      
		internal function frame17() : *
		{
			stop();
		}
      
		internal function frame25() : *
		{
			stop();
		}
      
		internal function frame33() : *
		{
			stop();
		}
      
		internal function frame41() : *
		{
			stop();
		}
      
		internal function frame49() : *
		{
			stop();
		}
      
		internal function frame57() : *
		{
			stop();
		}
      
		internal function frame65() : *
		{
			stop();
		}
      
		internal function frame73() : *
		{
			stop();
		}
      
		internal function frame81() : *
		{
			stop();
		}
      
		internal function frame89() : *
		{
			stop();
		}
      
		internal function frame97() : *
		{
			stop();
		}
      
		internal function frame105() : *
		{
			stop();
		}
      
		internal function frame113() : *
		{
			stop();
		}
      
		internal function frame121() : *
		{
			stop();
		}
      
		internal function frame129() : *
		{
			stop();
		}
      
		internal function frame137() : *
		{
			stop();
		}
      
		internal function frame145() : *
		{
			stop();
		}
      
		internal function frame153() : *
		{
			stop();
		}
      
		internal function frame161() : *
		{
			stop();
		}
      
		internal function frame169() : *
		{
			stop();
		}
      
		internal function frame177() : *
		{
			stop();
		}
      
		internal function frame185() : *
		{
			stop();
		}
      
		internal function frame193() : *
		{
			stop();
		}
      
		internal function frame201() : *
		{
			stop();
		}
      
		internal function frame209() : *
		{
			stop();
		}
      
		internal function frame217() : *
		{
			stop();
		}
      
		internal function frame225() : *
		{
			stop();
		}
      
		internal function frame233() : *
		{
			stop();
		}
      
		internal function frame241() : *
		{
			stop();
		}
      
		internal function frame249() : *
		{
			stop();
		}
      
		internal function frame257() : *
		{
			stop();
		}
      
		internal function frame265() : *
		{
			stop();
		}
      
		internal function frame273() : *
		{
			stop();
		}
      
		internal function frame281() : *
		{
			stop();
		}
      
		internal function frame289() : *
		{
			stop();
		}
      
		internal function frame297() : *
		{
			stop();
		}
      
		internal function frame305() : *
		{
			stop();
		}
      
		internal function frame313() : *
		{
			stop();
		}
      
		internal function frame321() : *
		{
			stop();
		}
      
		internal function frame329() : *
		{
			stop();
		}
      
		internal function frame337() : *
		{
			stop();
		}
      
		internal function frame345() : *
		{
			stop();
		}
      
		internal function frame353() : *
		{
			stop();
		}
      
		internal function frame361() : *
		{
			stop();
		}
      
		internal function frame369() : *
		{
			stop();
		}
      
		internal function frame377() : *
		{
			stop();
		}
      
		internal function frame385() : *
		{
			stop();
		}
      
		internal function frame393() : *
		{
			stop();
		}
      
		internal function frame401() : *
		{
			stop();
		}
      
		internal function frame409() : *
		{
			stop();
		}
      
		internal function frame417() : *
		{
			stop();
		}
      
		internal function frame425() : *
		{
			stop();
		}
      
		internal function frame433() : *
		{
			stop();
		}
      
		internal function frame441() : *
		{
			stop();
		}
      
		internal function frame449() : *
		{
			stop();
		}
      
		internal function frame457() : *
		{
			stop();
		}
      
		internal function frame465() : *
		{
			stop();
		}
      
		internal function frame473() : *
		{
			stop();
		}
      
		internal function frame481() : *
		{
			stop();
		}
	}
}