package driftkings.views.battle
{
   import driftkings.injector.BattleDisplayable;
   import net.wg.gui.battle.components.*;
   import net.wg.infrastructure.interfaces.IGraphicsOptimizationComponent;
   
	public class MinimapCentred extends BattleDisplayable
	{
		private var minimap:* = null;
		private var oldX:Number = 0;
		private var oldY:Number = 0;
		private var oldscaleX:Number = 0;
		private var oldscaleY:Number = 0;
		private var oldSize:Number = 0;
      
		public function MinimapCentred()
		{
			super();
		}
      
		override protected function onPopulate() : void
		{
			var topPosition:uint = 0;
			super.onPopulate();
			minimap = !!battlePage.hasOwnProperty("minimap") ? this.battlePage.minimap : null;
			if(minimap)
			{
				topPosition = battlePage.numChildren - 1;
				battlePage.setChildIndex(minimap, topPosition);
				App.graphicsOptimizationMgr.unregister(minimap as IGraphicsOptimizationComponent);
			}
		}
      
		public function as_minimapCentered(isEnabled:Boolean, scale:Number): void
		{
			updateMinimap(isEnabled, scale);
		}
      
		private function updateMinimap(isEnabled:Boolean, scale:Number): void
		{
			if(minimap)
			{
				if(isEnabled)
				{
					oldSize = minimap.currentSizeIndex;
					oldX = minimap.x;
					oldY = minimap.y;
					oldscaleX = minimap.scaleX;
					oldscaleY = minimap.scaleY;
					minimap.setAllowedSizeIndex(5);
					minimap.scaleX = scale;
					minimap.scaleY = scale;
					minimap.x = App.appWidth * 0.5 - minimap.currentWidth * 0.5 * scale;
					minimap.y = App.appHeight * 0.5 - minimap.currentHeight * 0.5 * scale;
				}
				else
				{
					minimap.scaleX = oldscaleX;
					minimap.scaleY = oldscaleY;
					minimap.setAllowedSizeIndex(oldSize);
					minimap.x = oldX;
					minimap.y = oldY;
				}
			}
		}
	}
}