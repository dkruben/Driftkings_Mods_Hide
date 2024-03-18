package driftkings.views.utils
{
	import flash.filters.DropShadowFilter;
	import flash.text.*;
	import driftkings.views.utils.Constants;
	
	public class TextExt extends TextField
	{
		public function TextExt(x:Number, y:Number, style:TextFormat, align:String, shadowSettings:Object, ui:*, enabled:Boolean = true)
		{
			super();
			if (style == null)
			{
				style = Constants.normalText;
			}
			this.x = x;
			this.y = y;
			this.width = 1;
			this.defaultTextFormat = style;
			this.antiAliasType = AntiAliasType.ADVANCED;
			this.autoSize = align;
			this.filters = [new DropShadowFilter(shadowSettings.distance, shadowSettings.angle, Utils.colorConvert(shadowSettings.color), shadowSettings.alpha, shadowSettings.blurX, shadowSettings.blurY, shadowSettings.strength, shadowSettings.quality)];
			this.selectable = false;
			this.multiline = true;
			this.visible = enabled;
			this.htmlText = "";
			ui.addChild(this);
		}
	}
}