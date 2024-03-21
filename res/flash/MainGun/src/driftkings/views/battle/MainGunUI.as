package driftkings.views.battle
{
	import flash.display.Bitmap;
	import flash.display.Sprite;
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	//
	import mods.common.BattleDisplayable;
	//
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.ProgressBar;
	import driftkings.views.utils.TextExt;
	
	public class MainGunUI extends BattleDisplayable
	{
		[Embed(source = "img/main_gun.png")]
		private var Gun_icon:Class;
		[Embed(source = "img/done.png")]
		private var Done_icon:Class;
		[Embed(source = "img/warning_1.png")]
		private var Warning_icon:Class;
		[Embed(source = "img/warning_2.png")]
		private var Warning_icon_cb:Class;
		
		private var icons:Vector.<Bitmap> = null;
		private var mainGun:TextExt       = null;
		private var progress:ProgressBar;
		//
		public var isColorBlind:Function;
		private var config:Object;
		
		public function MainGunUI()
		{
			super();
			this.addEventListener(Event.RESIZE, this._onResizeHandle);
		}
		
		override protected function onDispose():void
		{
			this.removeEventListener(Event.RESIZE, this._onResizeHandle);
			this.as_clearScene();
			super.onDispose();
		}
		
		public function as_clearScene():void
		{
			while (this.numChildren > 0)
			{
				this.removeChildAt(0);
			}
			this.mainGun = null;
			//App.utils.data.cleanupDynamicObject(this.config);
		}
		
		public function as_startUpdate(linkage:Object):void
		{
			this.icons = new <Bitmap>[new Gun_icon(), new Done_icon(), this.isColorBlind() ? new Warning_icon_cb() : new Warning_icon()];
			this.icons.fixed = true;
			
			var gun_icon:Bitmap     = this.icons[0];
			var done_icon:Bitmap    = this.icons[1];
			var warning_icon:Bitmap = this.icons[2];
			
			var _icons:Sprite       = new Sprite();
			_icons.y = 2;
			this.addChild(_icons);
			
			gun_icon.width = 26;
			gun_icon.height = 26;
			_icons.addChild(gun_icon);
			
			done_icon.width = 26;
			done_icon.height = 26;
			done_icon.visible = false;
			_icons.addChild(done_icon);
			
			warning_icon.width = 26;
			warning_icon.height = 26;
			warning_icon.alpha = 0.7;
			warning_icon.visible = false;
			_icons.addChild(warning_icon);
			
			var settings:Object = linkage;
			this.config = linkage
			this.x = (App.appWidth >> 1) + settings.x;
			this.y = settings.y;
			if (settings.progress_bar)
			{
				var colors:Object = linkage.global;
				this.mainGun = new TextExt(50, 0, Constants.middleText, TextFieldAutoSize.CENTER, this);
				this.progress = new ProgressBar(30, 24, 42, 4, colors.ally, colors.bgColor, 0.2);
				this.progress.setNewScale(0);
				this.addChild(this.progress);
			}
			else
			{
				this.mainGun = new TextExt(28, 0, Constants.largeText, TextFieldAutoSize.LEFT, this);
			}
		}
		
		override protected function onBeforeDispose():void
		{
			super.onBeforeDispose();
			this.mainGun = null;
			this.progress = null;
		}
		
		private function setDoneVisible(value:Boolean):void
		{
			if (this.icons[1].visible != value)
			{
				this.icons[1].visible = value
			}
		}
		
		public function as_gunData(value:int, max_value:int, warning:Boolean):void
		{
			var notAchived:Boolean = value > 0;
			this.icons[2].visible = warning && notAchived;
			if (notAchived)
			{
				this.mainGun.text = value.toString();
			}
			else
			{
				this.mainGun.text = "+" + Math.abs(value).toString();
			}
			this.setDoneVisible(!notAchived);
			if (this.progress)
			{
				this.progress.setNewScale(1.0 - (notAchived ? value : 0) / max_value)
			}
		}
		
		public function _onResizeHandle(event:Event):void
		{
			this.x = (App.appWidth >> 1) + this.config.x;
		}
	}
}