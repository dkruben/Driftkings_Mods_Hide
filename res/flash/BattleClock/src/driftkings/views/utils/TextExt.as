package driftkings.views.utils
{
	import flash.filters.DropShadowFilter;
	import flash.text.*;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.Utils;
	
	public class TextExt extends TextField
	{
		public function TextExt(x:Number, y:Number, align:String, textShadow:Object, ui:*, enabled:Boolean = true)
		{
			super();
			this.x = x;
			this.y = y;
			this.width = 1;
			this.antiAliasType = AntiAliasType.ADVANCED;
			this.autoSize = align;
			this.filters = [new DropShadowFilter(textShadow.distance, textShadow.angle, Utils.colorConvert(textShadow.color), textShadow.alpha, textShadow.blurX, textShadow.blurY, textShadow.strength, textShadow.quality)];
			this.selectable = false;
			this.multiline = true;
			this.visible = enabled;
			this.htmlText = "";
			ui.addChild(this);
		}
	}
}